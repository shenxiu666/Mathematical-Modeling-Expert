# 🧮 数学建模专家 Skill (Mathematical Modeling Expert)

> 一个专为数学建模竞赛（CUMCM / MCM / ICM）和实际业务优化问题设计的 Claude Code Skill。
>
> **核心能力**：现实问题抽象 → 数学模型构建 → 算法设计与求解 → 灵敏度分析与模型检验

---

## 📖 项目简介

本 Skill 蒸馏了顶尖应用数学与运筹学专家的认知模式，能够在 Claude Code 中提供专业级的数学建模辅助服务。

### 四大核心能力

| 能力 | 说明 |
|------|------|
| **🎯 问题翻译** | 将模糊的业务需求精准翻译为数学语言（目标函数、约束条件、决策变量） |
| **🏗️ 模型构建** | 从简化假设出发，逐层构建线性/非线性/整数规划、微分方程、图论等模型 |
| **⚙️ 算法设计** | 提供精确算法+启发式近似算法的完整求解策略，含复杂度分析 |
| **✅ 模型检验** | 强制灵敏度分析、参数扰动测试、鲁棒性评估，质疑模型的最脆弱假设 |

### 适用场景

- 🏆 全国大学生数学建模竞赛（CUMCM）
- 🌍 美国大学生数学建模竞赛（MCM/ICM）
- 🏢 企业运筹优化问题（物流调度、资源分配、选址问题）
- 📊 数据分析与评价决策（多属性决策、层次分析法）
- 🔬 科研中的动态系统建模（微分方程、系统动力学）

---

## 🚀 快速开始 (Quick Start)

### 1. 获取项目

```bash
git clone https://github.com/shenxiu666/Mathematical-Modeling-Expert.git
```

或直接从 GitHub 下载 ZIP 并解压。

### 2. 环境准备

**前置要求**：Python 3.10+、Git（可选）

推荐使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv venv

# 激活（Windows）
venv\Scripts\activate
# 激活（macOS/Linux）
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

依赖清单：

| 包 | 用途 |
|----|------|
| `numpy` | 数值计算基础设施 |
| `scipy` | 线性/非线性规划求解 |
| `pulp` | 整数规划建模（CBC 求解器） |
| `pandas` | 数据分析与 CSV 输出 |

### 3. 验证安装

```bash
# 运行评估测试（3/3 通过即为正常）
python tests/evaluate_skill.py

# 验证优化求解器
python tools/optimization_solver.py --input tests/mock_lp_problem.json

# 验证灵敏度分析器
python tools/sensitivity_analyzer.py --input tests/mock_sensitivity_params.json --summary-only
```

### 4. 在 Claude Code 中加载

```bash
# 在项目根目录启动 Claude Code
claude
```

Claude 将自动读取根目录的 `CLAUDE.md`，激活数学建模专家模式。之后所有建模问题都会按照标准 4-Phase 结构回答。

> **提示**：你也可以在 VS Code / JetBrains 的 Claude Code 插件中直接打开此项目目录。

---

## 📚 核心使用指南 (Usage Guide)

### 推荐 Prompt 模板

#### 模板 1：问题建模

```
请帮我将以下业务场景抽象为数学模型，并给出求解算法：

[描述你的问题，尽可能包含：
- 已知条件（数据、参数）
- 决策内容（要确定什么）
- 目标（最大化/最小化什么）
- 限制条件（资源、时间、容量等）]

请按照标准 4-Phase 结构输出，包含简化假设、符号说明表、
模型数学表达、算法伪代码和复杂度分析。
```

**示例**：

```
请帮我将以下场景建模：
"某外卖平台有 30 个骑手和 200 个订单，
每个订单有取餐点、送餐点和最晚送达时间。
如何分配订单使总配送距离最小化？"
```

#### 模板 2：灵敏度分析

```
请对当前模型进行灵敏度分析，指出最脆弱的假设，
并对关键参数进行 ±10% 和 ±20% 的扰动测试。

如果条件允许，请使用项目中的 sensitivity_analyzer.py
工具进行数值验证。
```

#### 模板 3：论文辅助

```
请帮我撰写数学建模论文的"模型假设"和"符号说明"章节。
我的模型是：[简要描述你的模型]
核心假设包括：[列出你的假设]
请用学术论文风格撰写，符合 CUMCM/MCM 论文规范。
```

### 辅助论文写作

本 Skill 可以辅助撰写以下论文章节：

| 章节 | 激活方式 |
|------|---------|
| **问题重述** | `请将以下赛题用数学语言重新表述：...` |
| **模型假设** | `请为我的模型撰写假设章节：...` |
| **符号说明** | `请生成以下变量的符号说明表：...` |
| **模型建立** | `请帮我推导/完善以下数学模型：...` |
| **算法设计** | `请为以下模型设计求解算法并分析复杂度：...` |
| **灵敏度分析** | `请对以下模型进行灵敏度分析：...` |
| **模型评价** | `请撰写模型优缺点与改进方向：...` |

---

## 🛠️ 辅助工具链说明 (Toolchain)

### 1. 优化求解器 (`tools/optimization_solver.py`)

**功能**：求解线性规划（LP）、整数规划（IP）和非线性规划（NLP）问题。

#### 命令行用法

```bash
# 基本用法
python tools/optimization_solver.py --input problem.json

# 将结果输出到 JSON 文件
python tools/optimization_solver.py --input problem.json --output result.json
```

#### LP 输入格式（线性规划）

```json
{
    "type": "lp",
    "objective": {
        "sense": "maximize",
        "coefficients": [3, 2]
    },
    "constraints": {
        "A_ub": [[1, 1], [2, 1]],
        "b_ub": [4, 5]
    },
    "bounds": [[0, null], [0, null]]
}
```

#### IP 输入格式（整数规划）

```json
{
    "type": "ip",
    "objective": {
        "sense": "minimize",
        "coefficients": [5, 7, 3]
    },
    "constraints": {
        "A_ub": [[1, 2, 0], [3, 1, 1]],
        "b_ub": [10, 9]
    },
    "bounds": [[0, 5], [0, null], [0, 3]],
    "integrality": [1, 1, 0]
}
```

> `integrality`: `1` = 整数变量，`0` = 连续变量

#### 输出格式

```
============================================================
优化求解报告
============================================================
问题类型: LP
求解状态: optimal
目标函数值: 9.000000
----------------------------------------
决策变量:
  x_0 = 1.000000
  x_1 = 3.000000
----------------------------------------
松弛变量:
  s_0 = 0.000000
  s_1 = 0.000000
----------------------------------------
迭代次数: 2
============================================================
```

### 2. 灵敏度分析器 (`tools/sensitivity_analyzer.py`)

**功能**：对模型参数进行单因子敏感性分析，生成**龙卷风图（Tornado Diagram）**所需的 CSV 数据。

#### 命令行用法

```bash
# 基本用法（输出到终端）
python tools/sensitivity_analyzer.py --input params.json

# 输出为 CSV 文件
python tools/sensitivity_analyzer.py --input params.json --output result.csv

# 仅输出龙卷风图摘要
python tools/sensitivity_analyzer.py --input params.json --summary-only
```

#### 输入格式

```json
{
    "base_params": {
        "alpha": 0.5,
        "beta": 1.2,
        "gamma": 2.0
    },
    "perturbations": [-0.2, -0.1, 0.1, 0.2],
    "output_key": "total_cost",
    "function_type": "expression",
    "objective_function": "alpha * x + beta * y - gamma * z",
    "function_vars": {
        "alpha": "alpha",
        "beta": "beta",
        "gamma": "gamma"
    },
    "fixed_inputs": {
        "x": 100,
        "y": 50,
        "z": 30
    }
}
```

支持 3 种目标函数类型：

| `function_type` | 说明 | 示例 |
|------|------|------|
| `expression` | 数学表达式 | `"a * x^2 + b * y"` |
| `linear` | 线性加权 | `coeffs: {"alpha": 2, "beta": 3}` |
| `cobb_douglas` | Cobb-Douglas 函数 | `A * x^α * y^β` |

#### 典型输出

```
龙卷风图摘要（按影响幅度降序排列）:
parameter  low_pct  low_output_change_pct  high_pct  high_output_change_pct  total_swing_pct
     beta    -20.0                  -24.0      20.0                    24.0             48.0
    gamma     20.0                  -24.0     -20.0                    24.0             48.0
    alpha    -20.0                  -20.0      20.0                    20.0             40.0
```

### Agent 自动调用机制

在建模对话中，Claude（建模专家）会在需要时**自动判断**是否调用这些工具：

- 当讨论到模型是否能解时 → 自动生成 JSON 并调用 `optimization_solver.py` 验证
- 当需要评估参数影响时 → 自动调用 `sensitivity_analyzer.py` 生成龙卷风图数据
- 你无需手动操作这些脚本！只需描述你的问题，Agent 会自主处理

---

## ⚠️ 已知边界与限制 (Limitations)

### 规模限制

| 问题类型 | 适用规模 | 大规模替代方案 |
|---------|---------|-------------|
| 线性规划（LP） | 变量 < 10⁵, 约束 < 10⁵ | Gurobi, CPLEX |
| 整数规划（IP） | 变量 < 10³, 0-1 变量 < 500 | Gurobi, SCIP |
| 非线性规划（NLP） | 变量 < 10³ | IPOPT, SNOPT |
| 灵敏度分析 | 参数 < 20 | Saltelli 全局敏感性方法 |

### 不适用场景

1. **三维计算流体力学（CFD）仿真**：本工具链不包含 N-S 方程数值求解器。请使用 COMSOL、ANSYS Fluent 或 OpenFOAM。
2. **超大规模组合优化**（百万级 0-1 变量）：CBC 开源求解器力不能及。请使用 Gurobi（学术免费）或 CPLEX。
3. **需要实时数据驱动的模型**：本 Skill 为离线建模工具，不含数据爬取或实时 API 调用能力。
4. **深度学习/复杂神经网络**：本 Skill 专注于基于物理/运筹的传统建模方法。

### 精度说明

- 本工具链适用于**竞赛级别的数值求解**，默认使用双精度浮点数（IEEE 754）
- 对于**工程级精度要求**（如航天轨道计算），建议使用专业求解器并进行误差传播分析
- IP 问题使用 CBC 求解器，对于数值病态问题可能收敛较慢

### 常见问题

**Q: 工具链输出乱码？**
A: 在 Windows 终端中可能出现编码问题。请在终端中执行 `chcp 65001` 切换到 UTF-8，或将输出重定向到文件。

**Q: PuLP 安装失败？**
A: 可尝试 `pip install pulp -i https://pypi.tuna.tsinghua.edu.cn/simple` 使用清华镜像源。

**Q: 如何贡献新的工具？**
A: 将新工具放入 `tools/` 目录，遵循 PEP 8 规范编写，并在 `README.md` 中补充说明即可。

---

## 📁 项目结构

```
.
├── CLAUDE.md                        # Skill 核心配置（角色、思维法则、输出结构）
├── README.md                        # 本文件 - 用户使用说明
├── DISTILLATION_REPORT.md           # Skill 蒸馏报告（含自评）
├── requirements.txt                 # Python 依赖
│
├── tools/                           # 辅助建模工具链
│   ├── optimization_solver.py       # 优化求解器
│   └── sensitivity_analyzer.py      # 灵敏度分析器
│
└── tests/                           # 测试文件
    ├── evaluate_skill.py            # 自动评估脚本
    ├── mock_lp_problem.json         # LP 测试数据
    ├── mock_ip_problem.json         # IP 测试数据
    └── mock_sensitivity_params.json # 灵敏度分析测试数据
```

---

## 📄 许可与引用

本项目为本地 Claude Code Skill，仅供建模竞赛和学术研究使用。

如果在竞赛或论文中受益于本 Skill 的辅助，欢迎引用：

```
受 "数学建模专家 Skill" 辅助完成。该工具基于 Claude Code 平台，
蒸馏了运筹优化与降维简化的建模方法论。
```

---

> **祝你建模顺利！May your models be elegant and your solutions optimal.** 🎯
