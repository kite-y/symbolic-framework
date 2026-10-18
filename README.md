# 象征物体系 · Symbolism System

> **把说不清的领域，拆成可推导的规则。**
> *Turning vague, intuition-based domains into derivable, reproducible, checkable rules.*

---

## English summary

A method — plus a small engine — for turning vague, intuition-based domains into **derivable, reproducible and checkable** rules.

**The core design decision: the engine contains no concrete domain vocabulary.**

All domain knowledge lives in a single, replaceable file (`engine/color_rules.py`). Verify it yourself: search `engine/engine.py` for **card names, suit names or colour names** — zero hits.

**The layer structure belongs to the domain too.** The engine ships with a default layer set, but the **domain layer may declare its own `LAYERS`** — the engine only reads it. (Verify: the shipped toy domain declares three layers, and `demo/demo_daily.py` prints both values side by side.)

Remaining residue: the identifier `card_id` and a few comments still carry tarot wording — **naming only, no behavioural effect**. See [`docs/引擎分层说明.md`](docs/引擎分层说明.md).

The engine only knows three things:

```
Element   (an atom: a symbol, a person, a scene, a mood)
Attribute (a seven-tier state: yin / yang / neutral, plus deep & decayed extremes)
Pairing   (two elements in relation → one of three states)
```

Tarot is **the first domain implemented**, not the point of the method.

**Two layers, kept apart:**

| | In this repository | Scope |
|---|---|---|
| **General method** | `docs/01_象征物体系.md` · `engine/engine.py` | domain-agnostic, no tarot vocabulary |
| **Domain layer (replaceable)** | `engine/color_rules.py` — a *toy* domain (light/shadow) | proves the boundary is real |
| **Tarot branch** | `docs/02_塔罗体系.md` · `docs/塔罗推理链.html` | **rules only — no implementation** |

| Path | What it is |
|---|---|
| `engine/engine.py` | **Generic layer** — attribute tiers, pairing table, state judging, depth modulation. No domain vocabulary. |
| `engine/color_rules.py` | **Domain layer (example)** — fully replaceable. What ships here is a *toy* domain (light/shadow, warm/cold), to prove the layer boundary. |
| `demo/demo_daily.py` | Runs the engine on a **non-tarot** domain. No dictionary required. |
| `docs/01_象征物体系.md` | **The method itself** — the general system, domain-agnostic. |
| `docs/02_塔罗体系.md` | **The method applied to tarot** — reversals, colour pairs, the 6-row table. |
| `docs/方法论流程图.html` | Interactive — the five steps, seven tiers, three states. |
| `docs/塔罗推理链.html` | Interactive — how one card becomes one paragraph. |

**Status (honest scope):** the generic engine + the example domain layer are complete and runnable. The **full domain dictionaries**, the 78-card generated data, and the spread-level pipeline are **not** in this repository.

Contact: **GitHub [@kite-y](https://github.com/kite-y)** — questions and corrections welcome via [Issues](https://github.com/kite-y/symbolic-system/issues).

---

## 这是什么（中文）

大部分"解读系统"（塔罗、占星、解梦、性格测评）都停在**结论**上——它告诉你"是什么"，不告诉你"**为什么是这样而不是那样**"。

中间缺了一层：**从可观察的东西，走到含义，再走到组合后的结论——这一段路是怎么走的？**

这个仓库补的就是这一段路。核心主张只有一句：

> **把"凭感觉"的解读，拆成可推导、可复现、可检查的规则。**

**它不承诺预测未来。** 它做的是：给你一套方法，让你从一个模糊的领域里，把结构捞出来。

---

## 通用 / 塔罗：两层，分开放

| | 在哪个文件 | 里面有什么 |
|---|---|---|
| **通用本体** | [`docs/01_象征物体系.md`](docs/01_象征物体系.md) · [`engine/engine.py`](engine/engine.py) | 元素 / 锚点 / 七档属性 / 三态关系。**不含任何领域词** |
| **领域层（可替换）** | [`engine/color_rules.py`](engine/color_rules.py) | 仓库里给的是**玩具领域**（光/影、暖/冷），用来证明"换一本字典就能换领域" |
| **塔罗分支** | [`docs/02_塔罗体系.md`](docs/02_塔罗体系.md) · [`docs/塔罗推理链.html`](docs/塔罗推理链.html) | **只有规则说明，没有实现**：牌面原文、78 张字典、牌阵都不在本仓库 |

> 一句话：**通用本体是"方法"，塔罗分支是"方法的一本字典"**。仓库带方法 + 一个玩具字典；塔罗那本字典只写了规则，没给数据。

---

## 核心设计：引擎与领域分离 ★

这是整个项目最重要的一条线，也是可以直接验证的：

```
┌──────────────────────────────────────────────┐
│  engine/engine.py        ← 通用层             │
│  · 七档属性（阴 / 阳 / 中 + 极 / 衰）          │
│  · 配对判定（6 行基础表 → 重叠 / 对碰 / 交汇）  │
│  · 深浅调制（进一档 / 退一档）                 │
│  · 标注解析、状态判定、字典读取接口             │
│  ★ 搜不到具体符号名（牌名 / 花色名 / 颜色名）    │
│  ★ 层结构也由领域层声明（引擎只读取）           │
│  ⚠️ 只剩 card_id 等命名残留（见下）             │
└──────────────────────────────────────────────┘
                      ↑ 只通过接口调用（5 个名字）
┌──────────────────────────────────────────────┐
│  engine/color_rules.py   ← 领域层（可整个替换）│
│  · 哪些符号参与对立                            │
│  · 每一对的激烈程度、是否改属性、含义怎么来      │
│  · 本领域有哪几层、各叫什么（LAYERS）           │
│  ★ 换领域时，只换这个文件                      │
└──────────────────────────────────────────────┘
```

### 自己验证（不用信我）

```bash
# 1) 引擎源码里有没有【具体符号名】？（预期：零命中）
grep -nE "塔罗|权杖|圣杯|宝剑|星币|正位|逆位|牌阵|Cups|Wands|Swords|Pentacles|黑色|白色|红色|黄色" engine/engine.py

# 2) 领域符号出现在哪？（预期：只在领域层）
grep -nE "光|影|暖|冷" engine/color_rules.py

# 3) 同一个引擎，换一个领域，跑得起来吗？
cd demo && python demo_daily.py
```

第 3 条跑出来的就是 [`demo/output.txt`](demo/output.txt) 里的内容——**那里面没有一个塔罗词**。

### ✅ 已知残留（已收窄 —— 我主动写出来，因为你能查到）

第 1 条命令零命中。下面这条**曾经也会命中**，现在范围已经缩到只剩命名：

```bash
# 4) 引擎里还剩哪些塔罗遗留？（预期：只剩命名层面的）
grep -nE "card_id|source_id|牌" engine/engine.py
```

| 残留 | 状态 |
|---|---|
| ~~`LAYERS = ("背景", "中景", "前景", "空间层")`~~ | ✅ **已抽出** —— 层结构现在由**领域层**声明（`color_rules.LAYERS`），引擎只读取；领域不声明时用默认四层 |
| `card_id` / `source_id` | ⚠️ 仍在：参数名还带"牌"的语境（**纯命名，不影响行为**） |
| 注释里的"牌"字 | ⚠️ 仍在：文档遗留 |

**现在的准确声称**：

> 引擎源码**不含任何具体符号名**（牌名 / 花色名 / 颜色名），**层结构也由领域层提供** —— 这两点都能自行 grep / 跑 demo 验证。
> 剩下的只是**命名**层面的遗留，不影响"换领域只换一个文件"这条性质。

> **工程上的含义**：换一个领域（占星 / 易经 / 一个业务概念体系），**引擎一行都不用改**，只换领域层。
> 这条线不是口号，是验收标准：**"引擎源码里搜不到具体符号名"**。
> **层结构也已归领域层**（`color_rules.LAYERS`）。剩下的只有**命名**层面的遗留（`card_id`、注释），见上面那节。

---

## 快速开始

```bash
cd demo
python demo_daily.py
```

不需要安装任何依赖，不需要字典，**标准库即可**。

> **IDE 报"未解析引用"（红线）？** 这是静态分析不跟 `sys.path` 的老问题，**不影响运行**。
> 脚本开头已经把 `engine/` 加进运行路径了，只是 IDE 不知道。让它知道：
> **PyCharm**：右键 `engine` 文件夹 → *Mark Directory as* → **Sources Root**，红线即消。
> **VS Code**：在 `.vscode/settings.json` 里加 `"python.analysis.extraPaths": ["./engine"]`。
> （该设置只影响本地 IDE，不进仓库。）

demo 会依次展示五件事：

| # | 展示什么 |
|---|---|
| ① | 一份解读怎么被算出来：元素 → 属性 → 配对 → 状态 → 关系位 |
| ② | 极 / 衰 折回基础三档（与领域无关） |
| ③ | 深浅：档位移动一格（引擎不含具体符号名） |
| ④ | **领域层可替换**：本仓库装的是【光 / 影 · 暖 / 冷】，不是颜色 |
| ⑤ | 同一张 6 行表，换个输入 → 结论完全不同 |

实际输出见 [`demo/output.txt`](demo/output.txt)。

---

## 四个设计取舍

这四条是我**主动做的克制**，也是这套方法与"凭感觉的解读"最本质的区别：

| # | 取舍 | 为什么 |
|---|---|---|
| **1** | **引擎不含领域词** | 否则这套东西只能用在塔罗上，换领域就得重写 |
| **2** | **不量化** | 属性只有档位，**不换算成数字、不做程度计量**。属性的变化只服务于含义 |
| **3** | **留白是设计，不是缺陷** | 三种状态里的「交汇」＝ 留白 / 选择空间，**不是"无法判断"**。一个不给留白的系统，会强迫给一切编造关系 |
| **4** | **可回溯** | 每句话要能指回具体元素；指不到 = 编的 |

第 3 条特别值得说：大多数系统是二值的（有关系 / 没关系），**这一层是特意留出来的弹性**。

---

## 目录结构

```
.
├── README.md                  本文
├── LICENSE
├── engine/
│   ├── engine.py              通用层（★ 无领域词）
│   └── color_rules.py         领域层（示例，可整个替换）
├── demo/
│   ├── demo_daily.py          非塔罗领域的 demo
│   └── output.txt             实际运行输出
└── docs/
      ├── 01_象征物体系.md        通用本体（对外版）
      ├── 02_塔罗体系.md          塔罗落地（对外版）
      ├── 引擎分层说明.md          分层设计与验收标准
      ├── 方法论流程图.html/.png   五步法可视化
      ├── 塔罗推理链.html/.png     塔罗那一支可视化
      └── 架构图.png              引擎分层图
```

---

## 状态与边界（不夸大）

**已完成并包含在本仓库**

- 通用引擎：属性档位 / 配对判定 / 深浅调制 / 标注解析
- 领域层的可替换设计（附示例领域层，可运行）
- 方法论（对外版）+ 架构图

**未包含在本仓库**

- 完整的领域字典（那是领域层资产）
- 具体领域的生成数据
- 牌阵（多元素结构）与多轮追问流程

**已知边界**

- 本方法描述的是**结构与关系**，不是"必定发生的未来"
- 锚点、属性这些定义来自作者判断（**是"偏见"，不是客观真理**）。写下来是因为：**只要规则一致，推导就是可复现的**
- **分层还不彻底**：层结构名称（背景 / 中景 / 前景 / 空间层）与 `card_id` 仍是引擎里的领域遗留 → 见[已知残留](#-已知残留我主动写出来因为你能查到)

---

## 许可

- **代码**（`engine/`、`demo/`）：MIT，见 [LICENSE](LICENSE)
- **文档与方法论**（`docs/`）：CC BY-NC 4.0

---

## 联系

**GitHub：[@kite-y](https://github.com/kite-y)**

> 有问题或指正，欢迎开 [Issue](https://github.com/kite-y/symbolic-system/issues)。
