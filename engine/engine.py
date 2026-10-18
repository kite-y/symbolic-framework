# -*- coding: utf-8 -*-
"""象征物体系 · 引擎

═══════════════════════════════════════════════════════════════════════════
这个文件是什么
═══════════════════════════════════════════════════════════════════════════

    把牌面的【文字】变成程序能用的【数据】。

    输入：  中景：一匹[[某种颜色]]的[[某个东西]]在奔跑
    输出：  ElementSet(
                elements     = [某颜色(中/…), 某象征物(阳/…)]
                combinations = [某颜色 + 某象征物 → 交汇/中偏阳]
            )

═══════════════════════════════════════════════════════════════════════════
颜色名只在 color_rules.py 里出现
═══════════════════════════════════════════════════════════════════════════

    这个文件里会出现"颜色"这个概念（因为颜色要走深浅/对立两条特殊规则，
    必须先把它从别的象征物里认出来），但【不出现任何具体的颜色名】。

    哪些名字算颜色 → 由字典 / 内置兜底名单决定
    哪几对会对立   → 在 color_rules.py 的 OPPOSITION_RECIPE 里

═══════════════════════════════════════════════════════════════════════════
目录（按依赖顺序，也是建议的阅读顺序）
═══════════════════════════════════════════════════════════════════════════

    第 1 节  属性档位         Attribute / DEEPEN / WEAKEN
    第 2 节  数据模型         Depth / ModType / State / Element / Combination / ElementSet
    第 3 节  标注解析         find_tags / depth_of
    第 4 节  状态判定         BASE / POLARITY / judge
    第 5 节  字典读取         load_dictionary / default_dictionary
    第 6 节  组装             build_element_set

    下面每一节都用 ═══ 分隔，可以按节跳读。
"""
import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum

# 注意：颜色对立规则的导入放在【文件最底部】。
# 因为 color_rules.py 需要这里的 Attribute，如果在这里就导入会造成循环。
# 放到最后，等 Attribute 等定义都完成了再导，就没有循环了。


# ═══════════════════════════════════════════════════════════════════════════
# 第 1 节 · 属性档位
# ═══════════════════════════════════════════════════════════════════════════
# 全体系的地基。只描述"属性有哪些档"以及"档位之间怎么移动"。

class Attribute(Enum):
    """七档属性。

    三档基础（阴 / 阳 / 中），加上深浅与对立可能产生的四档极值。
    """
    YIN = "阴"
    YANG = "阳"
    NEUTRAL = "中"
    EXTREME_YIN = "极阴"
    DECAY_YIN = "衰阴"
    EXTREME_YANG = "极阳"
    DECAY_YANG = "衰阳"


# 深浅：在档位上移动一格
#   "深"把基础档推向更强的形态；"浅"推向更弱的形态。
DEEPEN = {
    Attribute.YIN: Attribute.EXTREME_YIN,
    Attribute.YANG: Attribute.EXTREME_YANG,
    Attribute.NEUTRAL: Attribute.YIN,          # 中 + 深 → 阴
}

WEAKEN = {
    Attribute.YIN: Attribute.DECAY_YIN,
    Attribute.YANG: Attribute.DECAY_YANG,
    Attribute.NEUTRAL: Attribute.YANG,         # 中 + 浅 → 阳
}

# 深浅对含义的前缀
DEPTH_PREFIX = {
    "深": "过度",
    "浅": "缺乏",
}

# 注意：这里【没有】颜色名单。
# "哪些名字算颜色"由字典决定（字典的颜色表）。
# 内置兜底名单在 color_rules.py，因为那属于领域知识。


# ═══════════════════════════════════════════════════════════════════════════
# 第 2 节 · 数据模型
# ═══════════════════════════════════════════════════════════════════════════
# 全体系只有三个东西：
#     Element       一个原子（如"某个象征物"、"深某颜色"）
#     Combination   颜色 + 象征物   ← 这就是"整体象征物"
#     ElementSet    一张牌的全部

class Depth(Enum):
    """颜色前面的深浅前缀。"""
    NONE = "无"
    DEEP = "深"
    SHALLOW = "浅"
    MIXED = "交织"          # "深浅交织" → 不处理，走原有属性


class ModType(Enum):
    """这个元素的含义是被哪条规则改过的。"""
    NONE = "无"
    DEPTH = "深浅"
    OPPOSITION = "对立"


class State(Enum):
    """一次配对只可能产出这四种结果。

    ★ 静态不是"第四种判定结果" —— 它是"压根没配成组合"。
    """
    OVERLAP = "重叠"
    CLASH = "对碰"
    CONVERGE = "交汇"
    STATIC = "静态"


@dataclass
class Element:
    """一个原子。

    字段分两组：
        上半组 = 现在是什么（当前属性 / 当前含义）
        下半组 = 它原来是什么、被谁改过（可追溯）
    """
    name: str                 # 名称，如 "某象征物" / "某颜色"
    attribute: Attribute      # 当前属性（已被深浅/对立调制过）
    meanings: list            # 当前含义
    layer: str                # 来源层：背景 / 中景 / 前景 / 空间层
    raw: str                  # 回溯原文，如 "[[X]]" / "深[[Y]]"

    # 以下只有颜色元素才有值，其他元素为 None
    base_attribute: Attribute = None    # 字典里的原属性（未调制）
    depth: Depth = Depth.NONE
    mod_type: ModType = ModType.NONE
    opponent: str = None                # 对立时，对面是哪个颜色
    intensity: str = None               # 对立激烈程度
    original_meanings: list = None      # 被调制之前的含义


@dataclass
class Combination:
    """颜色 + 象征物。

    这就是"整体象征物"的构成单元 —— 歧点与瑕点消费的就是它。
    组合方式【与颜色深浅无关】：深浅只改变颜色这个元素自己携带的含义。
    """
    layer: str
    color: Element
    symbol: Element
    state: State
    bias: str                # 无 / 中偏阴 / 中偏阳


@dataclass
class ElementSet:
    """一张牌的全部元素与组合。"""
    source_id: str
    anchor: str              # 锚点（核心词），手写定死
    elements: list = field(default_factory=list)
    combinations: list = field(default_factory=list)

    @property
    def stated(self):
        """"具状态"的集合 —— 也就是整体象征物，供下游流动规则读取。"""
        return self.combinations


# ═══════════════════════════════════════════════════════════════════════════
# 第 3 节 · 标注解析
# ═══════════════════════════════════════════════════════════════════════════
# 把 [[ ]] 从原文里切出来。上游的 markdown 装饰（**加粗**、---、标题）全部忽略。
#
# 两种标注都返回：
#     完整   [[X]]      [[Y]]
#     残缺   [[间房屋]      [X]]       ← 少了一个括号
# 残缺的也返回（里面的字通常还能读），但单独列出来，方便做数据体检。

TAG = re.compile(r"\[\[([^\[\]]+)\]\]")
BROKEN_CLOSE = re.compile(r"^(?P<name>[^\[\]]{1,20})\](?!\])")      # [[xx]  → 少 ]
BROKEN_OPEN = re.compile(r"(?<!\[)\[(?P<name>[^\[\]]{1,20})\]\]")  # [xx]]  → 少 [

# 只有这三种前缀算数
DEEP_PREFIX = "深"
SHALLOW_PREFIX = "浅"
MIXED_PREFIX = "深浅"


def find_tags(text):
    """返回 (完整标注, 残缺标注)。

    完整 → [(名称, 起点, 终点), ...]
    残缺 → [(名称, 起点, 原文), ...]
    """
    complete = []
    broken = []
    taken = []

    for m in TAG.finditer(text):
        complete.append((m.group(1).strip(), m.start(), m.end()))
        taken.append((m.start(), m.end()))

    def inside(a, b):
        """这个位置是不是已经被完整标注占掉了。"""
        return any(s < b and a < e for s, e in taken)

    for m in BROKEN_OPEN.finditer(text):
        if not inside(m.start(), m.end()):
            broken.append((m.group("name").strip(), m.start(), m.group(0)))
    for m in BROKEN_CLOSE.finditer(text):
        if not inside(m.start(), m.end()):
            broken.append((m.group("name").strip(), m.start(), m.group(0)))

    broken.sort(key=lambda x: x[1])
    return complete, broken


def depth_of(text, start):
    """读取紧贴在标注【前面】的深浅前缀。

    只看前面几个字，因为前缀是紧贴着标注写的："深[[X]]"。

    这里有两个坑（都踩过）：
      1. 窗口要够宽 —— 最长的前缀"深浅交织"有 4 个字
      2. 必须先判"深浅交织" —— 它同时含"深"和"浅"，
         如果先判 endswith("深") 就会被截错

    "深浅" / "深浅交织" → MIXED（刻意不调制）
    "深"                → DEEP
    "浅"                → SHALLOW
    其他                → NONE
    """
    pre = text[max(0, start - 6):start]
    if MIXED_PREFIX in pre:
        return Depth.MIXED
    if pre.endswith(DEEP_PREFIX):
        return Depth.DEEP
    if pre.endswith(SHALLOW_PREFIX):
        return Depth.SHALLOW
    return Depth.NONE


# ═══════════════════════════════════════════════════════════════════════════
# 第 4 节 · 状态判定
# ═══════════════════════════════════════════════════════════════════════════
# 整个体系里唯一真正的"计算"。两个属性进去，一种状态出来。
#
# ★ 两套体系的区别（重要）
#     当前这套（领域用法）  只用基础表，判定结果只有【状态 + 偏向】，不输出强度。
#                           强度是一种"程度量化"，而这套体系里属性的变化
#                           只为含义服务，不做计量。
#     V3 通用方法论（后用）  会另有一套带强度的表。那属于通用层，
#                           等写通用层时重新定义，这里不预先保留。

A = Attribute
S = State

# 基础表 —— 照 V3 原文《关系变化规则》抄录，共 6 行
# 表里只写一个顺序；反过来的顺序由 match_table() 查镜像键。
BASE = {
    (A.YIN, A.YANG):        (S.CLASH,    "无"),
    (A.YIN, A.YIN):         (S.OVERLAP,  "无"),
    (A.YANG, A.YANG):       (S.OVERLAP,  "无"),
    (A.NEUTRAL, A.YIN):     (S.CONVERGE, "中偏阴"),
    (A.NEUTRAL, A.YANG):    (S.CONVERGE, "中偏阳"),
    (A.NEUTRAL, A.NEUTRAL): (S.OVERLAP,  "无"),
}

# 极 / 衰 折回基础三档
#   极阳、衰阳 本质还是阳 → 按"阳"查表
#   极阴、衰阴 本质还是阴 → 按"阴"查表
POLARITY = {
    A.YIN: A.YIN,
    A.DECAY_YIN: A.YIN,
    A.EXTREME_YIN: A.YIN,
    A.YANG: A.YANG,
    A.DECAY_YANG: A.YANG,
    A.EXTREME_YANG: A.YANG,
    A.NEUTRAL: A.NEUTRAL,
}


def base_of(attr):
    """把极 / 衰 折回基础三档。"""
    return POLARITY.get(attr)


def match_table(a, b):
    """在基础表里查 (a, b)，查不到就查镜像 (b, a)。

    表里只写了一个顺序，但配对是有先后的（谁跟谁配由数据决定），
    所以需要镜像查找。
    """
    if (a, b) in BASE:
        return BASE[(a, b)]
    if (b, a) in BASE:
        return BASE[(b, a)]
    return None


def judge(attr_a, attr_b):
    """判定一次配对，返回 (状态, 偏向)。

    【不返回强度】—— 当前这套不做程度量化。
    属性档位的变化只服务于含义，不参与计量。

    三种情况：
      1. 任何一端缺失 → 这次配对压根没发生 → (静态, None)
         【这不是判定结果】
      2. 折回三档后查到规则 → 返回 (状态, 偏向)
      3. 查不到 → (静态, None)
    """
    if attr_a is None or attr_b is None:
        return S.STATIC, None

    hit = match_table(base_of(attr_a), base_of(attr_b))
    if hit is None:
        return S.STATIC, None

    state, bias = hit
    return state, bias


def is_defined(attr_a, attr_b):
    """这两个属性能不能判。缺一端就算没定义。"""
    if attr_a is None or attr_b is None:
        return False
    return match_table(base_of(attr_a), base_of(attr_b)) is not None


# ═══════════════════════════════════════════════════════════════════════════
# 第 5 节 · 字典读取
# ═══════════════════════════════════════════════════════════════════════════
# 字典是【写死的】，不参与计算。它只回答两个问题：
#     这个象征物什么属性？
#     它有哪些含义？
#
# 主来源是用户维护的那份（data/tarot_source/tarot_dictionary*.py）。
# 读一次之后缓存成 data/dictionary.json，后面直接读缓存。

HERE = os.path.dirname(os.path.abspath(__file__))       # system/单牌
ROOT = os.path.dirname(os.path.dirname(HERE))           # 工作区根
CACHE_DIR = os.path.join(HERE, "cache")                 # 缓存目录（在单牌文件夹内）
CACHE_FILE = os.path.join(CACHE_DIR, "dictionary.json") # 字典缓存

# 字典来源：本文件夹下的 tarot_source/tarot_dictionary*.py
_SRC_DIR = os.path.join(HERE, "tarot_source")
_CANDIDATES = sorted(
    os.path.join(_SRC_DIR, f) for f in os.listdir(_SRC_DIR)
    if f.startswith("tarot_dictionary") and f.endswith(".py")
) if os.path.isdir(_SRC_DIR) else []
DICT_SOURCE = _CANDIDATES[-1] if _CANDIDATES else ""

# 旧来源（备选）：如需启用，设环境变量 DICT_FALLBACK 指向该文件
# ★ 不写死本地路径，免得公开后带上私人目录
V2_BACKUP = os.environ.get("DICT_FALLBACK", "")

# 哪些表里的东西算"颜色"
COLOR_TABLES = ("Upright_colors",)

# 哪些表里的东西算"象征物"
SYMBOL_TABLES = (
    "Upright_backgrounds", "Upright_compositions", "Upright_things",
    "Upright_figures", "Upright_postures", "Upright_counts", "Element",
)

_DEFAULT_DICT = None


def _exec_head(path):
    """执行源文件里 class/def 之前的内容，返回命名空间。

    因为字典都写在文件前部，而后面可能有 import 别的模块、
    或者有语法笔误，所以只执行前半段最稳。
    """
    if not path or not os.path.exists(path):
        return {}
    raw = open(path, encoding="utf-8-sig").read()
    cut = len(raw)
    for m in re.finditer(r"^(class|def)\s", raw, re.M):
        cut = m.start()
        break
    head = re.sub(r"^\s*(import|from)\s+.*$", "", raw[:cut], flags=re.M)
    ns = {}
    try:
        exec(compile(head, path, "exec"), ns)
    except Exception as e:
        print(f"  [提示] {os.path.basename(path)} 直接执行失败"
              f"({type(e).__name__})，改用逐块解析")
        ns = _exec_blockwise(raw)
    return ns


def _exec_blockwise(raw):
    """逐条赋值解析：`名字 = {...}`，一条一条试。"""
    ns = {}
    pat = re.compile(r"^(\w+)\s*=\s*\\?\s*(\{.*?^\})\s*$", re.M | re.S)
    for m in pat.finditer(raw):
        name, literal = m.group(1), m.group(2)
        try:
            ns[name] = eval(literal, {})
        except Exception:
            continue
    return ns


def _normalize(entry):
    """统一字段：属性 / 含义。兼容"象征"这个老字段名。"""
    if not isinstance(entry, dict):
        return None
    attr = entry.get("属性") or entry.get("attribute")
    meanings = (entry.get("含义") or entry.get("象征")
                or entry.get("meanings") or [])
    if isinstance(meanings, str):
        meanings = [meanings]
    return {"attribute": attr, "meanings": list(meanings)}


def build_dictionary(verbose=False):
    """拼出统一字典。

    返回::

        {
          "colors":  {"某颜色": {"attribute": "中", "meanings": [...]}, ...},
          "symbols": {"某象征物": {"attribute": "阳", "meanings": [...]}, ...},
        }
    """
    colors, symbols = {}, {}

    for path in (DICT_SOURCE, V2_BACKUP):
        ns = _exec_head(path)
        if not ns:
            continue
        for t in COLOR_TABLES:
            for name, entry in (ns.get(t) or {}).items():
                norm = _normalize(entry)
                if norm:
                    colors.setdefault(name, norm)
        for t in SYMBOL_TABLES:
            for name, entry in (ns.get(t) or {}).items():
                norm = _normalize(entry)
                if norm:
                    symbols.setdefault(name, norm)
        if verbose:
            print(f"  {os.path.basename(path)} → "
                  f"颜色 {len(colors)} 象征物 {len(symbols)}")

    return {"colors": colors, "symbols": symbols}


def load_dictionary(refresh=False):
    """取字典。优先读缓存，缓存不在或要求刷新就重建。"""
    if not refresh and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8-sig") as f:
            return json.load(f)
    d = build_dictionary()
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    return d


def default_dictionary():
    """默认字典，只加载一次（缓存在模块变量里）。"""
    global _DEFAULT_DICT
    if _DEFAULT_DICT is None:
        _DEFAULT_DICT = load_dictionary()
    return _DEFAULT_DICT


# ═══════════════════════════════════════════════════════════════════════════
# 第 6 节 · 组装
# ═══════════════════════════════════════════════════════════════════════════
# 把牌面原文变成 元素 和 组合。一张牌走三步（每层各走一遍）：
#
#     1. 解析   原文              → 元素（每处标注各自一个对象，互不共享）
#     2. 对立   按 [[颜色对立]] 标记，找出【那两个颜色】，只改它们
#     3. 组合   颜色 + 邻近象征物  → 组合
#
# 【调制是局部的】
#     同一张牌里，"深[[X]]"和"[[X]]"是两个不同的元素：
#       · 前者带深浅前缀 → 属性进一档、含义加"过度"
#       · 后者没前缀     → 属性仍是阴、含义原样
#     调制只作用于"那一处"，绝不串到别处。
#
# 【[[颜色对立]] 怎么用】
#     这个标记只指向【某两个颜色】，不是声明整层。
#     找法：从标记往前，最近的、能构成合法对立对的两个颜色。
#     找到之后交给 color_rules.resolve_opposition() 处理。

# 从某个位置往后找下一个 [[ ]]
LINK = re.compile(r"\[\[([^\[\]]+)\]\]")

# 允许出现在连接处的虚字（颜色和象征物之间）
ALLOWED_GAP = set("的 一和与、，。；; ,\u3000\t\n")
MAX_GAP = 3

MARKERS = ("颜色深浅", "颜色对立")
OPPOSITION_MARKER = "颜色对立"
# ★ 层结构属于【领域层】—— 下面是兜底默认值。
#   领域层可以声明自己的 LAYERS（"我有几层、各叫什么"）；
#   本文件【末尾】会用领域层的值覆盖它。领域没声明时保持默认，行为与以前一致。
DEFAULT_LAYERS = ("背景", "中景", "前景", "空间层")
LAYERS = DEFAULT_LAYERS          # ← 末尾可能被 color_rules.LAYERS 覆盖
TABLES = ("colors", "symbols", "elements")


# ───────────────────────────────────────────────────────────────────────────
# 6.0 颜色相关的小判断（具体颜色名不在这里，只判断"是不是颜色"）
# ───────────────────────────────────────────────────────────────────────────

def is_color(name, dictionary=None):
    """这个名字是不是颜色。

    ★ 只查字典的颜色表 —— 引擎里【不存颜色名单】。
      传字典是必需的：不传就一律当作"不是颜色"（宁可漏，也不错认）。
    """
    if not dictionary:
        return False
    return name in (dictionary.get("colors") or {})


def resolve_depth(base, depth):
    """把深浅施加到颜色的原属性上。

        深        → DEEPEN[base]（进一档）
        浅        → WEAKEN[base]（退一档）
        交织 / 无 → 原样
    """
    if depth in (Depth.NONE, Depth.MIXED):
        return base
    return DEEPEN[base] if depth is Depth.DEEP else WEAKEN[base]


def modulate_by_depth(meanings, depth):
    """深浅对含义：每条前面加"过度"或"缺乏"。无色深浅时原样返回。"""
    prefix = DEPTH_PREFIX.get(depth.value)
    if not prefix:
        return list(meanings)
    return [f"{prefix}{m}" for m in meanings]


def mod_type_for(depth):
    """深浅是不是真的改动了这个元素。"""
    return ModType.DEPTH if depth not in (Depth.NONE, Depth.MIXED) else ModType.NONE


# ───────────────────────────────────────────────────────────────────────────
# 6.1 主入口
# ───────────────────────────────────────────────────────────────────────────

def build_element_set(card_id, anchor, layers, dictionary=None):
    """组装一张牌的元素与组合。

    layers 形如 {"背景": "...", "中景": "...", "前景": "...", "空间层": "..."}

    dictionary 不传时用 default_dictionary()，结构::

        {
          "colors":  {"某颜色": {"attribute": "中", "meanings": [...]}, ...},
          "symbols": {"某象征物": {"attribute": "阳", "meanings": [...]}, ...},
        }
    """
    if dictionary is None:
        dictionary = default_dictionary()

    all_elements = []
    all_combos = []

    for layer in LAYERS:
        text = layers.get(layer, "")
        if not text:
            continue

        elements = _parse_elements(text, layer, dictionary)        # ① 解析
        _apply_opposition(text, elements, dictionary)              # ② 对立
        combos = _pair_combinations(text, elements, dictionary)    # ③ 组合

        all_elements.extend(elements)
        all_combos.extend(combos)

    return ElementSet(source_id=card_id, anchor=anchor,
                      elements=all_elements, combinations=all_combos)


# ───────────────────────────────────────────────────────────────────────────
# 6.2 解析：每处标注各生成一个独立对象
# ───────────────────────────────────────────────────────────────────────────

def _parse_elements(text, layer, dictionary):
    """把一层原文里的所有元素抠出来。"""
    tags, _broken = find_tags(text)
    out = []
    for name, start, end in tags:
        if name in MARKERS:
            continue
        out.append(_make_element(name, text, start, end, layer, dictionary))
    return out


def _make_element(name, text, start, end, layer, dictionary):
    """造一个元素。

    非颜色 → 属性和含义直接用字典里的值，不做任何处理。
    颜色   → 额外施加深浅规则（属性 + 含义），只作用于这一处。
    """
    original = list(_lookup(name, dictionary, "meanings") or [])
    base = _lookup(name, dictionary, "attribute")
    base = Attribute(base) if base else None
    raw = text[start:end]

    # 非颜色：一律原样
    if not is_color(name, dictionary):
        return Element(name=name, attribute=base, meanings=list(original),
                       layer=layer, raw=raw)

    # 颜色：看前面有没有深浅前缀
    depth = depth_of(text, start)
    return Element(
        name=name,
        attribute=resolve_depth(base, depth) if base else None,
        meanings=modulate_by_depth(original, depth),
        layer=layer, raw=raw,
        base_attribute=base, depth=depth,
        mod_type=mod_type_for(depth),
        original_meanings=original,
    )


# ───────────────────────────────────────────────────────────────────────────
# 6.3 对立：按标记找出那两个颜色，只改它们
# ───────────────────────────────────────────────────────────────────────────

def _apply_opposition(text, elements, dictionary):
    """读出 [[颜色对立]] 标记，找出它指向的那两个颜色，施加对立。

    ★ 标记只指向某两个颜色 —— 找法是"从标记往前，最近的能成对的两个颜色"。
      （V2 是直接取"最后两个颜色"，会拿成"白+绿"这种查不到的组合，
        结果 5 张牌的对立全丢了。这里是修掉那个 bug 的地方。）

    ★ 调制基于 original_meanings，否则重复配对会叠成"非非无"。
    """
    marker = text.find(f"[[{OPPOSITION_MARKER}]]")
    if marker < 0:
        return

    # 标记之前的颜色槽位，按位置排好
    slots = [(el, s, e) for el, s, e in _slots(text, elements)
             if is_color(el.name, dictionary) and s < marker]
    if len(slots) < 2:
        return

    pair = _nearest_opposing_pair(slots)
    if pair is None:
        return

    first, second = pair
    result = resolve_opposition(first.name, second.name,
                                first.original_meanings, second.original_meanings)
    if result is None:
        return

    for el, attr, means in ((first, result["attr_a"], result["meanings_a"]),
                            (second, result["attr_b"], result["meanings_b"])):
        if attr is not None:              # 只有黑白会给出属性，红白黄白是 None
            el.attribute = attr
        el.meanings = list(means)
        el.mod_type = ModType.OPPOSITION
    first.opponent, second.opponent = second.name, first.name
    first.intensity = second.intensity = result["intensity"]


def _nearest_opposing_pair(slots):
    """从后往前找最近的、能构成合法对立对的两个颜色。"""
    for i in range(len(slots) - 1, 0, -1):
        for j in range(i - 1, -1, -1):
            if is_opposition_pair(slots[j][0].name, slots[i][0].name):
                return slots[j][0], slots[i][0]
    return None


def _slots(text, elements):
    """把非标记标注与元素按顺序配对，得到 (元素, 起, 止)。"""
    tags = [t for t in find_tags(text)[0] if t[0] not in MARKERS]
    return [(el, t[1], t[2]) for el, t in zip(elements, tags)]


# ───────────────────────────────────────────────────────────────────────────
# 6.4 组合：颜色 + 邻近象征物
# ───────────────────────────────────────────────────────────────────────────

def _pair_combinations(text, elements, dictionary):
    """把每个颜色和紧跟在它后面的象征物配成一条组合。

    【链接窗口】颜色后面允许 0~3 个虚字再跟象征物：
        允许：的 / 一 / 和 / 与 / 空白 / 标点
        夹着别的内容就不配 —— 宁可漏配，也不乱配。
    """
    tags, _broken = find_tags(text)
    by_slot = _slot_map(tags, elements)
    combos = []
    used = set()

    for name, start, end in tags:
        if name in MARKERS:
            continue

        found = _find_link(text, end, dictionary)
        if not found:
            continue
        nxt, _gap = found

        color_el = by_slot.get((name, start))
        symbol_el = _first_named(elements, nxt, used)
        if color_el is None or symbol_el is None or color_el is symbol_el:
            continue

        used.add(id(symbol_el))
        state, bias = judge(color_el.attribute, symbol_el.attribute)
        combos.append(Combination(
            layer=color_el.layer, color=color_el, symbol=symbol_el,
            state=state, bias=bias,
        ))

    return combos


def _find_link(text, end, dictionary):
    """从 end 往后找"邻近的象征物标注"。返回 (名字, 间隔)，否则 None。

    ★ 这里不能用 ^ 锚点：调用方式是 LINK.search(文本, 位置)，
      而 ^ 只匹配整个字符串开头，加了就永远匹配不到中间的位置。
    """
    m = LINK.search(text, end)
    if not m:
        return None
    gap = text[end:m.start()]
    if len(gap) > MAX_GAP or any(ch not in ALLOWED_GAP for ch in gap):
        return None
    name = m.group(1).strip()
    if name in MARKERS or is_color(name, dictionary):
        return None                      # 标记、以及"颜色接颜色"都不算组合
    return name, gap


def _slot_map(tags, elements):
    usable = [t for t in tags if t[0] not in MARKERS]
    out = {}
    for (name, start, _e), el in zip(usable, elements):
        out.setdefault((name, start), el)
    return out


def _first_named(elements, name, used):
    """按名字找第一个还没被用过的元素。"""
    for el in elements:
        if el.name == name and id(el) not in used:
            return el
    return None


def _lookup(name, dictionary, field):
    """在 颜色表 / 象征物表 / 元素表 里依次找某个字段。"""
    for table in TABLES:
        entry = (dictionary.get(table) or {}).get(name)
        if entry and field in entry:
            return entry[field]
    return None


# ═══════════════════════════════════════════════════════════════════════════
# 最后 · 导入颜色对立规则
# ═══════════════════════════════════════════════════════════════════════════
# 放在文件最底部是【故意的】：
#   color_rules.py 里 `from .engine import Attribute` 需要 Attribute，
#   如果在本文件开头就导入 color_rules，那时 Attribute 还没定义 → 循环导入。
#   放到最后，等上面的定义全部完成再导，就没事了。

from color_rules import (           # noqa: E402（同目录）
    OPPOSITION_RECIPE,
    intensity_of,
    is_opposition_pair,
    resolve_opposition,
)


# ───────────────────────────────────────────────────────────────────────────
# 层结构：领域层说了算
# ───────────────────────────────────────────────────────────────────────────
#   领域层提供 LAYERS → 用它；没提供 → 保持上面的 DEFAULT_LAYERS。
#   这样换领域时，"有几层、各叫什么"由领域决定，**引擎不用改**。
#
#   ⚠️ 必须放在文件末尾：LAYERS 在第 576 行被 build_element_set() 使用，
#      那是函数体，调用时才会读全局值 —— 所以这里覆盖是有效的。

try:
    from color_rules import LAYERS as _DOMAIN_LAYERS      # noqa: E402
except ImportError:
    _DOMAIN_LAYERS = None

if _DOMAIN_LAYERS:
    LAYERS = tuple(_DOMAIN_LAYERS)

