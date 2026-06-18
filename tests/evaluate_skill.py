#!/usr/bin/env python3
"""
数学建模专家 Skill 自动化评估脚本
=====================================
设计 3 个典型数学建模测试用例，并检查模拟输出的文本中
是否包含建模专家的"思维锚点"关键词，以此评估 Skill 输出质量。

测试用例：
  1. 运筹调度问题：共享单车早高峰潮汐调度
  2. 动态演化问题：新型传染病传播趋势预测
  3. 评价决策问题：新能源汽车电池回收技术路线评估

用法：
    python evaluate_skill.py [--verbose] [--model-output-dir <path>]
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Optional


# ============================================================================
# 思维锚点关键词定义
# ============================================================================

# 锚点分为 5 个类别，对应建模专家的核心思维特征
ANCHOR_CATEGORIES = {
    "简化假设与抽象": [
        "简化假设", "核心假设", "假设条件", "基本假设",
        "模型假设", "理想化", "忽略次要", "抽象为",
        "assumption", "假设.*合理",
    ],
    "目标函数与约束": [
        "目标函数", "约束条件", "决策变量", "最优化",
        "最小化", "最大化", "objective", "constraint",
        "可行域", "可行解", "优化目标",
    ],
    "算法与求解策略": [
        "启发式算法", "贪心算法", "遗传算法", "模拟退火",
        "动态规划", "二分搜索", "时间复杂度", "近似算法",
        "精确求解", "数值求解", "迭代", "收敛",
        "heuristic", "algorithm", "复杂度",
    ],
    "灵敏度与鲁棒性": [
        "灵敏度分析", "鲁棒性", "参数扰动", "稳健性",
        "敏感性", "扰动测试", "参数敏感性", "模型检验",
        "鲁棒", "sensitivity", "robustness",
        "±10%", "±20%", "变化率",
    ],
    "模型结构与表达": [
        "符号说明", "数学表达", "模型构建", "量纲",
        "守恒", "微分方程", "差分方程", "状态方程",
        "平衡方程", "符号表", "模型框架",
    ],
}


# ============================================================================
# 3 个测试用例定义
# ============================================================================

@dataclass
class TestCase:
    """数学建模测试用例"""
    id: str
    category: str
    title: str
    description: str
    expected_anchors: list[str]  # 至少应出现的锚点类别
    min_anchor_count: int = 4    # 最少应匹配到的锚点关键词数


TEST_CASES = [
    TestCase(
        id="case_01",
        category="运筹调度",
        title="共享单车早高峰潮汐调度方案",
        description=(
            "某共享单车公司在一个拥有 50 个地铁站、200 个居民区的城市运营，"
            "拥有 10,000 辆单车和 50 辆调度车。早高峰（7:00-9:00）期间，"
            "居民区的单车需求急剧增加，而地铁站附近单车大量堆积。"
            "请设计一个最优的潮汐调度方案，最小化用户等待时间与调度成本。"
        ),
        expected_anchors=["简化假设与抽象", "目标函数与约束", "算法与求解策略", "灵敏度与鲁棒性"],
        min_anchor_count=5,
    ),
    TestCase(
        id="case_02",
        category="动态演化",
        title="新型传染病传播趋势预测",
        description=(
            "一种新型传染病具有以下特征：潜伏期 3-7 天，存在无症状感染者"
            "（占比约 30%），无症状感染者也具有传染性（传染力为有症状者的 60%）。"
            "某城市人口 500 万，初始感染者 100 人。请建立数学模型，"
            "预测未来 3 个月该传染病的传播趋势，并评估不同防控措施的效果。"
        ),
        expected_anchors=["简化假设与抽象", "模型结构与表达", "灵敏度与鲁棒性"],
        min_anchor_count=4,
    ),
    TestCase(
        id="case_03",
        category="评价决策",
        title="新能源汽车电池回收技术路线评估",
        description=(
            "新能源汽车动力电池退役潮即将到来。现有三种回收技术路线："
            "A) 湿法冶金（回收率高但污染大），B) 干法回收（成本低但回收率低），"
            "C) 生物浸出（环保但技术不成熟）。需从经济（成本/收益）、"
            "环境（碳排放/污染）、社会（就业/安全）三个维度进行综合评估，"
            "选择最优技术路线。"
        ),
        expected_anchors=["简化假设与抽象", "模型结构与表达", "灵敏度与鲁棒性"],
        min_anchor_count=4,
    ),
]


# ============================================================================
# 评估函数
# ============================================================================

def count_anchors(text: str) -> dict:
    """
    统计文本中匹配到的思维锚点关键词。

    Parameters
    ----------
    text : str
        待评估的建模输出文本

    Returns
    -------
    dict
        {
            "category_counts": {类别名: 匹配次数},
            "total_matches": 总匹配次数,
            "matched_keywords": [匹配到的具体关键词列表],
            "category_match_status": {类别名: bool（是否至少匹配 1 次）}
        }
    """
    category_counts = {}
    matched_keywords = []
    category_match_status = {}

    for category, patterns in ANCHOR_CATEGORIES.items():
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                count += len(matches)
                for m in matches:
                    matched_keywords.append({"category": category, "keyword": m, "pattern": pattern})
        category_counts[category] = count
        category_match_status[category] = count > 0

    total = sum(category_counts.values())
    return {
        "category_counts": category_counts,
        "total_matches": total,
        "matched_keywords": matched_keywords,
        "category_match_status": category_match_status,
    }


def evaluate_case(test_case: TestCase, model_output: str) -> dict:
    """
    对单个测试用例的输出进行评估。

    Parameters
    ----------
    test_case : TestCase
        测试用例定义
    model_output : str
        Skill 针对该测试用例的输出文本

    Returns
    -------
    dict
        评估结果
    """
    anchor_result = count_anchors(model_output)

    # 检查预期锚点类别是否全部出现
    missing_categories = []
    for expected_cat in test_case.expected_anchors:
        if not anchor_result["category_match_status"].get(expected_cat, False):
            missing_categories.append(expected_cat)

    # 判定
    all_categories_met = len(missing_categories) == 0
    enough_keywords = anchor_result["total_matches"] >= test_case.min_anchor_count
    passed = all_categories_met and enough_keywords

    return {
        "case_id": test_case.id,
        "case_title": test_case.title,
        "passed": passed,
        "total_anchor_matches": anchor_result["total_matches"],
        "min_required": test_case.min_anchor_count,
        "expected_categories": test_case.expected_anchors,
        "missing_categories": missing_categories,
        "category_coverage": anchor_result["category_match_status"],
        "category_counts": anchor_result["category_counts"],
        "matched_keywords_sample": [kw["keyword"] for kw in anchor_result["matched_keywords"][:10]],
        "failure_reason": (
            None if passed else
            f"缺失类别: {missing_categories}" if missing_categories else
            f"关键词数量不足: {anchor_result['total_matches']} < {test_case.min_anchor_count}"
        ),
    }


def run_all_tests(model_outputs: dict) -> dict:
    """
    运行所有测试用例。

    Parameters
    ----------
    model_outputs : dict
        {case_id: 模型输出文本}

    Returns
    -------
    dict
        包含 summary 和 details 的完整评估报告
    """
    results = []
    for tc in TEST_CASES:
        output = model_outputs.get(tc.id, "")
        if not output:
            result = {
                "case_id": tc.id,
                "case_title": tc.title,
                "passed": False,
                "total_anchor_matches": 0,
                "min_required": tc.min_anchor_count,
                "expected_categories": tc.expected_anchors,
                "missing_categories": tc.expected_anchors,
                "category_coverage": {},
                "category_counts": {},
                "matched_keywords_sample": [],
                "failure_reason": "未提供模型输出文本（model_outputs 中缺少该 case_id）",
            }
        else:
            result = evaluate_case(tc, output)
        results.append(result)

    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)

    return {
        "summary": {
            "total_cases": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate": f"{passed_count / total_count * 100:.1f}%" if total_count > 0 else "N/A",
        },
        "details": results,
    }


# ============================================================================
# 模拟输出生成器（用于自测）
# ============================================================================

def generate_mock_output(test_case: TestCase) -> str:
    """
    为测试用例生成一个模拟的建模专家回答（用于演示评估流程）。

    在实际使用中，这里应该由 Claude 读取 CLAUDE.md 后生成。
    此函数仅用于脚本的独立自测。

    Parameters
    ----------
    test_case : TestCase
        测试用例

    Returns
    -------
    str
        模拟的建模专家输出
    """
    if test_case.id == "case_01":
        return """
## Phase 1: 问题重述与核心假设

### 1.1 原始问题重述
将共享单车潮汐调度问题抽象为一个带时间窗的车辆路径问题（VRPTW）的变体。
已知：50个地铁站、200个居民区位置，10000辆单车初始分布...
目标函数：最小化用户等待时间与调度车运营成本之和。

### 1.2 核心假设
- 假设1：简化假设早高峰期间用户需求是确定性的（基于历史平均值）
- 假设2：调度车以恒定速度行驶（简化假设交通状况均匀）
- 假设3：假设每个用户等待超过5分钟即产生惩罚成本

### 符号说明
| 符号 | 含义 | 单位 |
|------|------|------|
| x_ij | 从i到j的单车调度数量 | 辆 |
| t_w | 用户等待时间 | 分钟 |

## Phase 2: 模型构建与数学表达

### 2.1 目标函数
最小化 Z = α·∑(用户等待时间) + β·∑(调度车行驶距离)
其中 α, β 为权重系数，经过量纲分析确保单位一致性。

### 2.2 约束条件
- 流量守恒约束：每个站点的单车净流入 = 骑行到达 - 骑行离开 + 调度到达 - 调度离开
- 容量约束：每个站点单车数量不超过最大容量
- 非负约束：所有决策变量 ≥ 0

## Phase 3: 算法设计与求解策略

考虑到问题的 NP-Hard 特性，我们提出两阶段启发式算法：
1. 第一阶段：基于聚类的需求预测（使用 k-means 将 200 个居民区聚合为 20 个需求区）
2. 第二阶段：改进的贪心调度算法
   - 时间复杂度：O(n²log n)，n 为站点数量
   - 通过模拟退火微调解体局部最优问题

## Phase 4: 灵敏度分析与模型检验

### 灵敏度分析
对关键参数进行 ±10% 和 ±20% 的扰动测试：
- α 权重：用户等待成本权重变化 ±20% 时，总成本波动在 ±8% 内
- 单车初始分布：扰动 ±15% 时，最优调度方案基本不变
- 结果表明模型具有较好的鲁棒性

### 模型优缺点
- 优点：计算可扩展、能处理大规模场景
- 缺点：未考虑实时动态需求变化
"""
    elif test_case.id == "case_02":
        return """
## Phase 1: 问题重述与核心假设

### 1.1 原始问题重述
建立考虑潜伏期和无症状感染者的扩展 SEIR 动力学模型。

### 1.2 核心假设
- 假设1：简化假设人口均匀混合（忽略年龄结构和空间分布）
- 假设2：康复者获得永久免疫（在研究时段 3 个月内）
- 假设3：假设潜伏期也具有传染性但传染力较低
- 假设4：忽略出生和自然死亡（3 个月内人口总量基本不变）

### 符号说明
| 符号 | 含义 | 单位 |
|------|------|------|
| S(t) | t时刻易感者数量 | 人 |
| E(t) | t时刻潜伏期人数 | 人 |

## Phase 2: 模型构建与数学表达

基于守恒律建立微分方程组：
dS/dt = -β·S·(I + ε·A) / N
dE/dt = β·S·(I + ε·A)/N - σ·E
...

量纲检查：β 量纲为 1/时间，σ·E 量纲为 人/时间，方程两边量纲一致 ✓

## Phase 3: 算法设计与求解策略

使用四阶 Runge-Kutta 方法进行数值求解，步长 Δt = 0.1 天。
通过 Python 的 scipy.integrate.solve_ivp 实现。
时间复杂度：O(T/Δt)，其中 T=90 天，可快速完成。

## Phase 4: 灵敏度分析与模型检验

### 灵敏度分析
对基本再生数 R₀ 进行参数扰动测试：
- β ±20% → 峰值感染人数变化 ±35%（模型对该参数较敏感）
- γ（康复率）±20% → 峰值变化 ±18%
- ε（无症状传染力）±20% → 峰值变化 ±12%

### 鲁棒性讨论
模型对 β 参数最敏感，这提示我们应重点关注传染率的准确估计。
通过蒙特卡洛模拟进行不确定性传播分析。
"""
    elif test_case.id == "case_03":
        return """
## Phase 1: 问题重述与核心假设

### 1.1 问题重述
这是一个典型的多属性决策分析（MADA）问题。
需要在经济、环境、社会三维度下对三种电池回收技术进行综合评估和排序。

### 1.2 核心假设
- 假设1：简化假设三个维度相互独立（实际上环境和经济存在耦合）
- 假设2：各评价指标的权重可通过 AHP（层次分析法）确定
- 假设3：假设技术成熟度可用 TRL（技术就绪水平）量化

### 符号说明
| 符号 | 含义 |
|------|------|
| w_j | 第j个准则的权重 |
| a_ij | 方案i在准则j下的得分 |

## Phase 2: 模型构建与数学表达

采用 TOPSIS（逼近理想解排序法）结合熵权法构建评价模型。

目标函数：最大化各方案与正理想解的相对接近度 C_i*

约束条件包括：所有指标评分标准化到 [0,1] 区间、权重和为 1。

## Phase 3: 算法设计与求解策略

步骤：
1. 数据标准化（向量规范化）
2. 熵权法计算客观权重
3. 构建加权标准化矩阵
4. 确定正负理想解
5. 计算相对接近度并排序

整体算法复杂度 O(m·n)，可在 Excel 或 Python 中轻松实现。

## Phase 4: 灵敏度分析与模型检验

### 灵敏度分析
对权重进行 ±20% 的扰动测试：
- 经济权重 ±20% → 排序变化较小（仅方案 A 和 B 在边界情况交换）
- 环境权重增加 20% → 方案 C 排名上升 1 位
- 结论：评价结果具有较好的鲁棒性

### 模型优缺点
- 优点：方法成熟、可解释性强、计算简单
- 缺点：TOPSIS 假设指标间独立，不适用于强耦合的评价体系
"""
    else:
        return "无匹配的测试用例。"


# ============================================================================
# 主函数
# ============================================================================

def print_report(report: dict, verbose: bool = False):
    """格式化打印评估报告。"""
    summary = report["summary"]
    details = report["details"]

    print("=" * 70)
    print("  数学建模专家 Skill 自动评估报告")
    print("=" * 70)
    print()
    print(f"测试用例总数: {summary['total_cases']}")
    print(f"通过: {summary['passed']} | 失败: {summary['failed']}")
    print(f"通过率: {summary['pass_rate']}")
    print()

    print("-" * 70)
    for case_result in details:
        status_icon = "[PASS]" if case_result["passed"] else "[FAIL]"
        print(f"  [{status_icon}] {case_result['case_id']}: {case_result['case_title']}")
        print(f"       匹配关键词数: {case_result['total_anchor_matches']} (最小要求: {case_result['min_required']})")
        print(f"       预期锚点类别: {', '.join(case_result['expected_categories'])}")
        if case_result["missing_categories"]:
            print(f"       缺失类别: {', '.join(case_result['missing_categories'])}")
        print(f"       类别覆盖: {case_result['category_coverage']}")
        if verbose and case_result.get("matched_keywords_sample"):
            print(f"       匹配示例: {case_result['matched_keywords_sample']}")
        if case_result.get("failure_reason"):
            print(f"       失败原因: {case_result['failure_reason']}")
        print()
    print("=" * 70)

    # 汇总建议
    if summary["failed"] > 0:
        print("改进建议:")
        print("  1. 确保输出包含全部 4 个 Phase 的标准结构")
        print("  2. 检查是否明确列出了核心假设（Phase 1）")
        print("  3. 在 Phase 3 中提供具体的算法名称和时间复杂度")
        print("  4. 在 Phase 4 中明确展示参数扰动测试和灵敏度分析结论")
    else:
        print("[PASS] 所有测试用例通过！Skill 输出质量符合建模专家标准。")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="数学建模专家 Skill 自动化评估",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python evaluate_skill.py                    # 使用模拟数据自测
  python evaluate_skill.py --verbose          # 详细输出
        """,
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细匹配信息")
    args = parser.parse_args()

    print("注意: 当前使用模拟输出进行自测。")
    print("在实际使用中，请将 Claude 针对各测试用例的真实输出替换 model_outputs 字典。")
    print()

    # 生成模拟输出并运行测试
    model_outputs = {}
    for tc in TEST_CASES:
        model_outputs[tc.id] = generate_mock_output(tc)

    report = run_all_tests(model_outputs)
    print_report(report, verbose=args.verbose)

    # 返回退出码
    if report["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
