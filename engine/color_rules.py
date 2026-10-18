# -*- coding: utf-8 -*-
"""领域层（示例）—— 这个文件是【可以整个替换】的。

★ 引擎末尾有一句：

      from color_rules import (OPPOSITION_RECIPE, intensity_of,
                               is_opposition_pair, resolve_opposition)

  那句 import 规定了这个文件的【接口】，
  但**不规定它的内容**。

★ 在塔罗领域里，这个文件装的是"颜色对立"（例如 黄白 / 红白 / 黑白）。

  在这个示例里，它装的是一个**完全不同的领域**：【光 / 影】与【暖 / 冷】。

  **引擎不知道这两者的区别** —— 它只调用接口。

★ 所以：**换领域时，你只需要换掉这个文件。**

★ 本仓库附带的这一版是**示例**，不含任何完整领域数据。
"""
from engine import Attribute

# ═══════════════════════════════════════════════════════════════════════════
# 层结构（领域自己声明：我有几层、各叫什么）
# ═══════════════════════════════════════════════════════════════════════════
# ★ 引擎里有个默认值（塔罗那套「背景 / 中景 / 前景 / 空间层」）。
#   这个示例领域与塔罗无关，所以声明自己的三层 —— **引擎会读这个值**。
#   这一条正是"换领域时引擎一行都不用改"的最后一环。

LAYERS = ("表层", "里层", "底层")

# ═══════════════════════════════════════════════════════════════════════════
# 本领域里"会参与对立"的符号
# ═══════════════════════════════════════════════════════════════════════════

LIGHT = "光"
SHADOW = "影"
WARM = "暖"
COLD = "冷"

OPPOSITION_COLORS = {LIGHT, SHADOW, WARM, COLD}


def can_oppose(name):
    """这个符号会不会产生对立。"""
    return name in OPPOSITION_COLORS


# ═══════════════════════════════════════════════════════════════════════════
# 对立配方表
# ═══════════════════════════════════════════════════════════════════════════
# 字段含义（引擎的接口约定）：
#   intensity    激烈程度
#   change_attr  是否改属性
#   attr_self    改属性时，本色变成什么
#   attr_other   改属性时，对面变成什么
#   meanings     手写调制含义；None 表示用"非X"生成

OPPOSITION_RECIPE = {
    # 改属性的一对
    frozenset({LIGHT, SHADOW}): {
        "intensity": "最激烈",
        "change_attr": True,
        "attr_self": Attribute.EXTREME_YANG,     # 光 → 极阳
        "attr_other": Attribute.EXTREME_YIN,     # 影 → 极阴
        "meanings": None,                        # None = 用"非X"生成
    },
    # 不改属性的一对，含义手写
    frozenset({WARM, COLD}): {
        "intensity": "较温和",
        "change_attr": False,
        "meanings": {
            WARM: ["向内聚拢", "柔和的持续"],
            COLD: ["向外散开", "清晰的停顿"],
        },
    },
}

# 合法对立对（从上面那张表推导，不重复写）
OPPOSITION_PAIRS = tuple(OPPOSITION_RECIPE)


# ═══════════════════════════════════════════════════════════════════════════
# 定位：只回答"算不算对立"
# ═══════════════════════════════════════════════════════════════════════════

def find_opposition(sym_a, sym_b):
    """【只定位】返回这一对的配方；不成对立返回 None。"""
    pair = frozenset({sym_a, sym_b})
    if len(pair) < 2:                      # 同一个符号不算一对
        return None
    return OPPOSITION_RECIPE.get(pair)


def is_opposition_pair(sym_a, sym_b):
    """这两个符号算不算合法对立对。"""
    return find_opposition(sym_a, sym_b) is not None


def intensity_of(sym_a, sym_b):
    """激烈程度；不成对立返回 None。"""
    recipe = find_opposition(sym_a, sym_b)
    return recipe["intensity"] if recipe else None


# ═══════════════════════════════════════════════════════════════════════════
# 推导：只负责给出结果
# ═══════════════════════════════════════════════════════════════════════════

def resolve_opposition(sym_a, sym_b, meanings_a=None, meanings_b=None):
    """施加一对符号的对立，返回结果 dict；不成对立返回 None。

    返回::

        {
          "intensity":  激烈程度,
          "attr_a":     A 的新属性 或 None（None = 属性不变）,
          "attr_b":     B 的新属性 或 None,
          "meanings_a": A 调制后的含义,
          "meanings_b": B 调制后的含义,
        }
    """
    recipe = find_opposition(sym_a, sym_b)
    if recipe is None:
        return None

    meanings_a = list(meanings_a or [])
    meanings_b = list(meanings_b or [])

    # ---- 属性 ----
    if recipe["change_attr"]:
        attr_a = recipe["attr_self"] if sym_a == LIGHT else recipe["attr_other"]
        attr_b = recipe["attr_self"] if sym_b == LIGHT else recipe["attr_other"]
    else:
        attr_a = attr_b = None             # 属性一个都不动

    # ---- 含义 ----
    handwritten = recipe["meanings"]
    if handwritten is None:
        # 用"非X"生成：一边的含义 = 对【另一边】的原含义逐个加"非"
        new_a = [f"非{m}" for m in meanings_b] or ["绝对对立"]
        new_b = [f"非{m}" for m in meanings_a] or ["绝对对立"]
    else:
        new_a = list(handwritten.get(sym_a, meanings_a))
        new_b = list(handwritten.get(sym_b, meanings_b))

    return {
        "intensity": recipe["intensity"],
        "attr_a": attr_a,
        "attr_b": attr_b,
        "meanings_a": new_a,
        "meanings_b": new_b,
    }
