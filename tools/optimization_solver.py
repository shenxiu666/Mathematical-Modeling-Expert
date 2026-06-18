#!/usr/bin/env python3
"""
优化求解器 (Optimization Solver)
=================================
支持线性规划（LP）、整数规划（IP）和非线性规划（NLP）的求解。
接受 JSON 格式输入，输出最优解、目标值、松弛变量和对偶变量。

线性规划使用 scipy.optimize.linprog 或 pulp 求解；
整数规划使用 pulp（CBC 求解器）；
非线性规划使用 scipy.optimize.minimize。

用法：
    python optimization_solver.py --input problem.json [--output result.json]

输入 JSON 格式（线性规划示例）：
{
    "type": "lp",                    // "lp" | "ip" | "nlp"
    "objective": {
        "sense": "minimize",         // "minimize" | "maximize"
        "coefficients": [3, 2]       // 目标函数系数 c
    },
    "constraints": {
        "A_ub": [[1, 1], [2, 1]],    // 不等式约束矩阵 A_ub @ x <= b_ub
        "b_ub": [4, 5],
        "A_eq": null,                // 等式约束矩阵 A_eq @ x == b_eq
        "b_eq": null
    },
    "bounds": [[0, null], [0, null]], // 变量边界 [lower, upper]
    "integrality": null,             // 整数约束（仅 IP）: [0, 1] 表示 {连续, 整数}
    "options": {}                     // 求解器额外选项
}

作者：数学建模专家 Skill 工具链
"""

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Optional, Union

# numpy 和 scipy 在函数内部懒加载，确保 --help 在未安装依赖时也能运行
# 抑制 scipy 的过时警告
warnings.filterwarnings("ignore", category=DeprecationWarning)


def solve_lp(
    coefficients: list,
    sense: str,
    A_ub: Optional[list],
    b_ub: Optional[list],
    A_eq: Optional[list],
    b_eq: Optional[list],
    bounds: Optional[list],
    options: Optional[dict] = None,
) -> dict:
    """
    使用 scipy.optimize.linprog 求解线性规划问题。

    Parameters
    ----------
    coefficients : list
        目标函数系数
    sense : str
        "minimize" 或 "maximize"
    A_ub : list or None
        不等式约束矩阵
    b_ub : list or None
        不等式约束右端向量
    A_eq : list or None
        等式约束矩阵
    b_eq : list or None
        等式约束右端向量
    bounds : list or None
        变量边界
    options : dict or None
        求解器选项

    Returns
    -------
    dict
        包含 status, objective_value, variables, slack, duals 的字典
    """
    import numpy as np
    from scipy.optimize import linprog

    c = np.array(coefficients, dtype=float).copy()
    if sense == "maximize":
        c = -c  # linprog 默认最小化

    opts = options.copy() if options else {}
    opts.setdefault("disp", False)

    result = linprog(
        c=c,
        A_ub=np.array(A_ub) if A_ub else None,
        b_ub=np.array(b_ub) if b_ub else None,
        A_eq=np.array(A_eq) if A_eq else None,
        b_eq=np.array(b_eq) if b_eq else None,
        bounds=bounds if bounds else (0, None),
        method="highs",
        options=opts,
    )

    obj_val = result.fun
    if sense == "maximize":
        obj_val = -obj_val if obj_val is not None else None

    return {
        "status": "optimal" if result.success else result.message,
        "success": result.success,
        "objective_value": float(obj_val) if obj_val is not None else None,
        "variables": result.x.tolist() if result.success else None,
        "slack": result.slack.tolist() if result.success and hasattr(result, "slack") else None,
        "nit": result.nit if hasattr(result, "nit") else None,
    }


def solve_ip_pulp(
    coefficients: list,
    sense: str,
    A_ub: Optional[list],
    b_ub: Optional[list],
    A_eq: Optional[list],
    b_eq: Optional[list],
    bounds: Optional[list],
    integrality: Optional[list],
    options: Optional[dict] = None,
) -> dict:
    """
    使用 PuLP (CBC) 求解混合整数线性规划。

    Parameters
    ----------
    coefficients, sense, A_ub, b_ub, A_eq, b_eq, bounds, options :
        同 solve_lp
    integrality : list or None
        整数标记: 0 = 连续, 1 = 整数

    Returns
    -------
    dict
        包含 status, objective_value, variables 的字典
    """
    try:
        import pulp
    except ImportError:
        return {
            "status": "pulp_not_installed",
            "success": False,
            "error": "PuLP 库未安装。请运行: pip install pulp",
            "objective_value": None,
            "variables": None,
        }

    n_vars = len(coefficients)
    sense_flag = pulp.LpMinimize if sense == "minimize" else pulp.LpMaximize
    prob = pulp.LpProblem("OptimizationProblem", sense_flag)

    # 创建变量
    vars_list = []
    for i in range(n_vars):
        lb = bounds[i][0] if bounds and i < len(bounds) and bounds[i][0] is not None else 0
        ub = bounds[i][1] if bounds and i < len(bounds) and bounds[i][1] is not None else None
        is_int = integrality[i] == 1 if integrality and i < len(integrality) else False
        cat = pulp.LpInteger if is_int else pulp.LpContinuous
        var = pulp.LpVariable(f"x_{i}", lowBound=lb, upBound=ub, cat=cat)
        vars_list.append(var)

    # 目标函数
    prob += pulp.lpSum(coefficients[i] * vars_list[i] for i in range(n_vars))

    # 不等式约束
    if A_ub and b_ub:
        for row_idx, row in enumerate(A_ub):
            lhs = pulp.lpSum(row[j] * vars_list[j] for j in range(n_vars))
            prob += (lhs <= b_ub[row_idx])

    # 等式约束
    if A_eq and b_eq:
        for row_idx, row in enumerate(A_eq):
            lhs = pulp.lpSum(row[j] * vars_list[j] for j in range(n_vars))
            prob += (lhs == b_eq[row_idx])

    # 求解
    solver_opts = options or {}
    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)

    raw_status = pulp.LpStatus[prob.status]
    status_map = {
        "Optimal": "optimal",
        "Not Solved": "not_solved",
        "Infeasible": "infeasible",
        "Unbounded": "unbounded",
        "Undefined": "undefined",
    }

    return {
        "status": status_map.get(raw_status, raw_status),
        "success": raw_status == "Optimal",
        "objective_value": pulp.value(prob.objective) if raw_status == "Optimal" else None,
        "variables": [pulp.value(v) for v in vars_list] if raw_status == "Optimal" else None,
    }


def solve_nlp(
    objective_fn_desc: str,
    coefficients: list,
    sense: str,
    constraints_desc: Optional[list],
    bounds: Optional[list],
    options: Optional[dict] = None,
) -> dict:
    """
    使用 scipy.optimize.minimize 求解简单非线性规划。
    支持二次目标函数形式：a * x^2 + b * x + c

    Parameters
    ----------
    objective_fn_desc : str
        目标函数描述（"quadratic" 或 "general"）
    coefficients : list
        二次函数的系数 [a, b, c]（若为 quadratic）
    sense : str
        "minimize" 或 "maximize"
    constraints_desc : list or None
        约束列表，每个约束为 {"type": "ineq", "fun_desc": "linear", "coeffs": [...]}
    bounds : list or None
        变量边界
    options : dict or None
        求解器选项

    Returns
    -------
    dict
        包含 status, objective_value, variables 的字典
    """
    import numpy as np
    from scipy.optimize import minimize, Bounds, LinearConstraint

    if objective_fn_desc == "quadratic":
        a, b, c_coef = coefficients[0], coefficients[1], coefficients[2]
        sign = 1 if sense == "minimize" else -1

        def objective(x):
            return sign * (a * x[0] ** 2 + b * x[0] + c_coef)
    else:
        return {
            "status": "unsupported_objective",
            "success": False,
            "error": "目前仅支持 quadratic 目标函数。对于一般 NLP 问题，请使用特定的求解器。",
            "objective_value": None,
            "variables": None,
        }

    # 约束处理
    scipy_constraints = []
    if constraints_desc:
        for con in constraints_desc:
            if con.get("fun_desc") == "linear" and con.get("type") == "ineq":
                coeffs = con["coeffs"]
                lb_val = con.get("lb", -np.inf)
                ub_val = con.get("ub", np.inf)

                def con_fun(x, coeffs=coeffs):
                    return np.dot(coeffs, x)

                if np.isfinite(lb_val) and np.isfinite(ub_val):
                    lc = LinearConstraint(np.array([coeffs]), lb_val, ub_val)
                elif np.isfinite(lb_val):
                    lc = LinearConstraint(np.array([coeffs]), lb_val, np.inf)
                else:
                    lc = LinearConstraint(np.array([coeffs]), -np.inf, ub_val)
                scipy_constraints.append(lc)

    x0 = np.zeros(len(coefficients) - 1)  # 二次函数系数去掉常数项
    opts = options or {}
    opts.setdefault("disp", False)

    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=Bounds(
            [b[0] if b and b[0] is not None else -np.inf for b in (bounds or [[]])],
            [b[1] if b and len(b) > 1 and b[1] is not None else np.inf for b in (bounds or [[]])],
        ),
        constraints=scipy_constraints,
        options={"disp": False, "maxiter": opts.get("maxiter", 1000)},
    )

    return {
        "status": "optimal" if result.success else result.message,
        "success": result.success,
        "objective_value": float(sign * result.fun) if result.success else None,
        "variables": result.x.tolist() if result.success else None,
        "nit": result.nit if hasattr(result, "nit") else None,
    }


def solve_from_json(input_data: dict) -> dict:
    """
    根据 JSON 输入自动识别问题类型并求解。

    Parameters
    ----------
    input_data : dict
        JSON 格式的问题描述

    Returns
    -------
    dict
        求解结果
    """
    problem_type = input_data.get("type", "lp")
    objective = input_data.get("objective", {})
    constraints = input_data.get("constraints", {})
    bounds = input_data.get("bounds")
    options = input_data.get("options", {})

    sense = objective.get("sense", "minimize")
    coefficients = objective.get("coefficients", [])

    if problem_type in ("lp", "ip"):
        if problem_type == "ip":
            integrality = input_data.get("integrality", [0] * len(coefficients))
            return solve_ip_pulp(
                coefficients=coefficients,
                sense=sense,
                A_ub=constraints.get("A_ub"),
                b_ub=constraints.get("b_ub"),
                A_eq=constraints.get("A_eq"),
                b_eq=constraints.get("b_eq"),
                bounds=bounds,
                integrality=integrality,
                options=options,
            )
        else:
            # 纯 LP：优先用 scipy（更快），如果不可行则用 PuLP 提供更详细信息
            result = solve_lp(
                coefficients=coefficients,
                sense=sense,
                A_ub=constraints.get("A_ub"),
                b_ub=constraints.get("b_ub"),
                A_eq=constraints.get("A_eq"),
                b_eq=constraints.get("b_eq"),
                bounds=bounds,
                options=options,
            )
            if not result["success"]:
                # 回退到 PuLP 获取更多信息
                return solve_ip_pulp(
                    coefficients=coefficients,
                    sense=sense,
                    A_ub=constraints.get("A_ub"),
                    b_ub=constraints.get("b_ub"),
                    A_eq=constraints.get("A_eq"),
                    b_eq=constraints.get("b_eq"),
                    bounds=bounds,
                    integrality=[0] * len(coefficients),
                    options=options,
                )
            return result

    elif problem_type == "nlp":
        return solve_nlp(
            objective_fn_desc=objective.get("type", "general"),
            coefficients=coefficients,
            sense=sense,
            constraints_desc=constraints,
            bounds=bounds,
            options=options,
        )
    else:
        return {
            "status": "unknown_type",
            "success": False,
            "error": f"不支持的问题类型: {problem_type}。支持: lp, ip, nlp",
            "objective_value": None,
            "variables": None,
        }


def format_output(result: dict, input_data: dict) -> str:
    """格式化输出为人类可读的文本。"""
    lines = []
    lines.append("=" * 60)
    lines.append("优化求解报告")
    lines.append("=" * 60)
    lines.append(f"问题类型: {input_data.get('type', 'lp').upper()}")
    lines.append(f"求解状态: {result['status']}")

    if result.get("error"):
        lines.append(f"错误信息: {result['error']}")
        return "\n".join(lines)

    if result["success"]:
        lines.append(f"目标函数值: {result['objective_value']:.6f}")
        lines.append("-" * 40)
        lines.append("决策变量:")
        if result["variables"]:
            for i, val in enumerate(result["variables"]):
                lines.append(f"  x_{i} = {val:.6f}")
        else:
            lines.append("  (无)")
        if result.get("slack"):
            lines.append("-" * 40)
            lines.append("松弛变量:")
            for i, val in enumerate(result["slack"]):
                lines.append(f"  s_{i} = {val:.6f}")
        if result.get("nit") is not None:
            lines.append("-" * 40)
            lines.append(f"迭代次数: {result['nit']}")
    else:
        lines.append("模型无可行解或求解失败。请检查您的约束条件。")
        lines.append("建议检查：")
        lines.append("  1. 约束是否互相矛盾？")
        lines.append("  2. 变量边界是否合理？")
        lines.append("  3. 整数约束是否导致不可行？")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="数学建模优化求解器 - 支持 LP/IP/NLP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python optimization_solver.py --input problem.json
  python optimization_solver.py --input problem.json --output result.json
        """,
    )
    parser.add_argument(
        "--input", "-i", type=str, required=True, help="输入 JSON 文件路径"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="输出 JSON 文件路径（可选）"
    )
    args = parser.parse_args()

    # 读取输入
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 输入文件 '{args.input}' 不存在。", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取文件失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 求解
    result = solve_from_json(input_data)

    # 输出
    print(format_output(result, input_data))

    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存至: {args.output}")


if __name__ == "__main__":
    main()
