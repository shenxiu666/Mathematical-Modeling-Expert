#!/usr/bin/env python3
"""
灵敏度分析器 (Sensitivity Analyzer)
=====================================
对数学模型的参数进行系统扰动分析，评估模型鲁棒性。
支持多参数的单因子敏感性分析，输出龙卷风图（Tornado Diagram）CSV 数据。

用法：
    python sensitivity_analyzer.py --input model_params.json [--output result.csv]

输入 JSON 格式：
{
    "base_params": {
        "param_alpha": 0.5,
        "param_beta": 1.2,
        "param_gamma": 2.0
    },
    "perturbations": [-0.2, -0.1, 0.1, 0.2],
    "output_key": "total_cost",       // 要观测的输出变量名
    "objective_function": "a * x + b * y - c * z",
    "function_vars": {
        "a": "param_alpha",
        "b": "param_beta",
        "c": "param_gamma"
    },
    "fixed_inputs": {                 // 不在扰动范围内的固定输入
        "x": 100,
        "y": 50,
        "z": 30
    }
}

或者使用内建的简单函数模式：
{
    "base_params": {...},
    "perturbations": [...],
    "output_key": "...",
    "function_type": "linear",        // 支持: "linear", "cobb_douglas"
    "function_coeffs": {...}
}

作者：数学建模专家 Skill 工具链
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

# numpy 和 pandas 在函数内部懒加载，确保 --help 在未安装依赖时也能运行


class SensitivityAnalyzer:
    """
    灵敏度分析器。

    对模型的每个参数进行独立扰动，记录目标输出值的变化，
    用于生成龙卷风图所需的排名数据。

    Attributes
    ----------
    base_params : dict
        基准参数值
    perturbations : list[float]
        扰动比例列表
    """

    def __init__(self, base_params: dict, perturbations: list[float]):
        """
        初始化灵敏度分析器。

        Parameters
        ----------
        base_params : dict
            {参数名: 基准值}
        perturbations : list[float]
            扰动比例，例如 [-0.2, -0.1, 0.1, 0.2]
        """
        self.base_params = base_params.copy()
        self.perturbations = sorted(perturbations)
        self._base_output = None

    def _evaluate_base(self, func: Callable) -> float:
        """计算基准参数下的目标值。"""
        if self._base_output is None:
            self._base_output = func(**self.base_params)
        return self._base_output

    def analyze(
        self,
        func: Callable,
        output_key: str = "output",
    ) -> pd.DataFrame:
        """
        执行灵敏度分析。

        Parameters
        ----------
        func : callable
            目标函数，接受 **base_params 作为关键字参数，返回数值
        output_key : str
            输出变量的名称

        Returns
        -------
        pandas.DataFrame
            包含列: parameter, perturbation_pct, param_value, output_value, pct_change
        """
        import pandas as pd

        base_val = self._evaluate_base(func)
        records = []

        for param_name, base_param_val in self.base_params.items():
            for pert in self.perturbations:
                # 构建扰动后的参数
                perturbed_params = self.base_params.copy()
                new_val = base_param_val * (1 + pert)
                perturbed_params[param_name] = new_val

                try:
                    perturbed_output = func(**perturbed_params)
                    if base_val != 0:
                        pct_change = (perturbed_output - base_val) / abs(base_val) * 100
                    else:
                        pct_change = float("inf") if perturbed_output != 0 else 0.0
                except Exception as e:
                    perturbed_output = None
                    pct_change = None

                records.append({
                    "parameter": param_name,
                    "perturbation_pct": round(pert * 100, 1),
                    "param_value": round(new_val, 6),
                    "output_value": round(perturbed_output, 6) if perturbed_output is not None else None,
                    "pct_change": round(pct_change, 4) if pct_change is not None else None,
                })

        df = pd.DataFrame(records)
        return df

    def tornado_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成龙卷风图摘要：每个参数的最大影响（± 方向）。

        Parameters
        ----------
        df : pd.DataFrame
            analyze() 返回的完整结果

        Returns
        -------
        pd.DataFrame
            每个参数一行：最大正影响和最大负影响
        """
        import pandas as pd

        summary_records = []
        for param_name in df["parameter"].unique():
            sub = df[df["parameter"] == param_name].dropna(subset=["pct_change"])
            if sub.empty:
                continue
            max_positive = sub.loc[sub["pct_change"].idxmax()]
            max_negative = sub.loc[sub["pct_change"].idxmin()]

            summary_records.append({
                "parameter": param_name,
                "low_pct": max_negative["perturbation_pct"],
                "low_output_change_pct": max_negative["pct_change"],
                "high_pct": max_positive["perturbation_pct"],
                "high_output_change_pct": max_positive["pct_change"],
                "total_swing_pct": round(
                    abs(max_positive["pct_change"] - max_negative["pct_change"]), 4
                ),
            })

        summary = pd.DataFrame(summary_records)
        summary = summary.sort_values("total_swing_pct", ascending=False)
        return summary


def build_function_from_expr(expr: str, var_mapping: dict, fixed_inputs: dict) -> Callable:
    """
    从字符串表达式和变量映射构建目标函数。

    Parameters
    ----------
    expr : str
        数学表达式，如 "a*x + b*y - c*z"
    var_mapping : dict
        参数名到表达式变量的映射，如 {"a": "param_alpha", ...}
    fixed_inputs : dict
        固定输入变量的值，如 {"x": 100, "y": 50, "z": 30}

    Returns
    -------
    callable
        接受 **base_params 的函数
    """
    import numpy as np

    # 构建安全求值环境
    safe_dict = {"__builtins__": {}, "sin": np.sin, "cos": np.cos, "exp": np.exp,
                 "log": np.log, "sqrt": np.sqrt, "abs": abs, "pi": np.pi, "e": np.e}

    # 反转映射：参数名 -> 表达式变量
    param_to_var = {v: k for k, v in var_mapping.items()}

    def func(**kwargs):
        local_vars = fixed_inputs.copy()
        for param_name, value in kwargs.items():
            var_name = param_to_var.get(param_name)
            if var_name:
                local_vars[var_name] = value
            else:
                local_vars[param_name] = value
        safe_dict.update(local_vars)
        try:
            return float(eval(expr, {"__builtins__": {}}, safe_dict))
        except Exception as e:
            raise ValueError(f"表达式求值失败: '{expr}' with vars={local_vars}. 错误: {e}")

    return func


def build_linear_function(coeffs: dict) -> Callable:
    """
    构建线性目标函数。

    Parameters
    ----------
    coeffs : dict
        {参数名: 系数}，如 {"alpha": 2, "beta": -1}

    Returns
    -------
    callable
        func(alpha=..., beta=...) -> sum(coeff * value)
    """

    def func(**kwargs):
        total = 0.0
        for param_name, coeff in coeffs.items():
            total += coeff * kwargs.get(param_name, 0)
        return total

    return func


def build_cobb_douglas_function(coeffs: dict, a: float = 1.0) -> Callable:
    """
    构建 Cobb-Douglas 生产函数形式的目标函数。

    Y = A * prod(param_i^{exponent_i})

    Parameters
    ----------
    coeffs : dict
        {参数名: 指数}
    a : float
        全要素生产率参数

    Returns
    -------
    callable
    """

    def func(**kwargs):
        product = a
        for param_name, exponent in coeffs.items():
            product *= kwargs.get(param_name, 1) ** exponent
        return product

    return func


def load_input(input_path: str) -> dict:
    """从 JSON 文件加载输入数据，含错误处理。"""
    path = Path(input_path)
    if not path.exists():
        print(f"错误: 输入文件 '{input_path}' 不存在。", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 验证必要字段
    if "base_params" not in data:
        print("错误: 输入 JSON 必须包含 'base_params' 字段。", file=sys.stderr)
        sys.exit(1)
    if "perturbations" not in data:
        print("错误: 输入 JSON 必须包含 'perturbations' 字段。", file=sys.stderr)
        sys.exit(1)

    return data


def main():
    parser = argparse.ArgumentParser(
        description="数学建模灵敏度分析器 - 参数扰动与龙卷风图数据生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python sensitivity_analyzer.py --input model_params.json
  python sensitivity_analyzer.py --input model_params.json --output result.csv
  python sensitivity_analyzer.py --input model_params.json --output result.csv --summary-only
        """,
    )
    parser.add_argument(
        "--input", "-i", type=str, required=True, help="输入 JSON 文件路径"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="输出 CSV 文件路径（可选，不指定则只打印到终端）"
    )
    parser.add_argument(
        "--summary-only", action="store_true",
        help="仅输出龙卷风图摘要（不输出每个扰动点的详细数据）"
    )
    args = parser.parse_args()

    # 加载输入
    input_data = load_input(args.input)

    base_params = input_data["base_params"]
    perturbations = input_data["perturbations"]
    output_key = input_data.get("output_key", "output")

    # 构建目标函数
    func_type = input_data.get("function_type", "expression")

    if func_type == "expression" or "objective_function" in input_data:
        expr = input_data.get("objective_function", "")
        var_mapping = input_data.get("function_vars", {})
        fixed_inputs = input_data.get("fixed_inputs", {})
        if not expr:
            print("错误: 需要 'objective_function' 字段指定数学表达式。", file=sys.stderr)
            sys.exit(1)
        target_func = build_function_from_expr(expr, var_mapping, fixed_inputs)
        print(f"目标函数: {expr}")
    elif func_type == "linear":
        coeffs = input_data.get("function_coeffs", {})
        target_func = build_linear_function(coeffs)
        print(f"线性目标函数, 系数: {coeffs}")
    elif func_type == "cobb_douglas":
        coeffs = input_data.get("function_coeffs", {})
        a = input_data.get("a_parameter", 1.0)
        target_func = build_cobb_douglas_function(coeffs, a)
        print(f"Cobb-Douglas 目标函数, A={a}, 指数: {coeffs}")
    else:
        print(f"错误: 不支持的目标函数类型 '{func_type}'。", file=sys.stderr)
        sys.exit(1)

    # 执行分析
    analyzer = SensitivityAnalyzer(base_params, perturbations)

    try:
        base_val = target_func(**base_params)
    except Exception as e:
        print(f"错误: 基准参数下目标函数计算失败: {e}", file=sys.stderr)
        sys.exit(1)

    df = analyzer.analyze(target_func, output_key)
    summary = analyzer.tornado_summary(df)

    # 输出
    print("=" * 60)
    print("灵敏度分析报告")
    print("=" * 60)
    print(f"基准参数: {base_params}")
    print(f"基准输出值 ({output_key}): {base_val:.6f}")
    print(f"扰动范围: {[f'{p*100:+.0f}%' for p in perturbations]}")
    print()
    print("龙卷风图摘要（按影响幅度降序排列）:")
    print("-" * 60)
    print(summary.to_string(index=False))

    if not args.summary_only:
        print()
        print("详细扰动数据:")
        print("-" * 60)
        print(df.to_string(index=False))

    # 保存 CSV
    if args.output:
        output_path = Path(args.output)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n详细数据已保存至: {args.output}")

        # 同时保存摘要
        summary_path = output_path.with_stem(output_path.stem + "_summary")
        summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
        print(f"龙卷风图摘要已保存至: {summary_path}")


if __name__ == "__main__":
    main()
