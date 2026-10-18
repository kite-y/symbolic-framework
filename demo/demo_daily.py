# -*- coding: utf-8 -*-
"""demo —— 用同一套引擎，跑一个【非塔罗】领域。

★ 这个 demo 要证明的事

    引擎不认识"塔罗"。它只认识【元素 + 属性 + 配对】。
    换一个领域，只换领域层（engine/color_rules.py），引擎一行都不用改。

★ 依赖范围

    只 import engine.py（通用层）+ color_rules.py（**本仓库附带的示例领域层**）。
    **不读任何完整字典、不含任何塔罗数据。**

★ 怎么跑

    python demo/demo_daily.py
"""
import os
import sys

# 控制台编码保护（和 入口.py 同款）：避免在 GBK 终端上崩掉
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "engine"))

from engine import (Attribute as A, judge, base_of,
                    DEEPEN, WEAKEN, DEPTH_PREFIX)


# ═══════════════════════════════════════════════════════════════════════════
# ① 领域层 —— 随便写一个日常领域（与塔罗无关）
# ═══════════════════════════════════════════════════════════════════════════
# 每条 = (元素名, 锚点（它的核心含义）, 属性)

DOMAIN = {
    "一个人走进一场聚会": [
        ("这个人",   "适应性",   A.NEUTRAL),
        ("这场聚会", "强娱乐性", A.YANG),
    ],
    '"爱" 与 "伤心"': [
        ("爱",   "说不清、但依赖触发点的联结", A.NEUTRAL),
        ("伤心", "说得清的低落",               A.YIN),
    ],
    "一个人身上的多个标签": [
        ("对外的人",   "职业性", A.YANG),
        ("对内的人",   "松弛",   A.YIN),
        ("在家人面前", "被照顾", A.NEUTRAL),
    ],
}

# 引擎算出来的是【状态】；含义由【关系位】读出来。
# 这层映射属于"展示"，不属于引擎。
POSITION = {
    "重叠": "和谐位（相关、和谐）",
    "对碰": "冲突位（矛盾、相对）",
    "交汇": "调和位（留白、选择）",
    "静态": "没有配成组合（这不是判定结果）",
}


def show_pairing():
    print("=" * 74)
    print("  ① 一份解读是怎么被算出来的：元素 → 属性 → 配对 → 状态 → 关系位")
    print("=" * 74)

    for title, elements in DOMAIN.items():
        print(f"\n【{title}】")
        for name, anchor, attr in elements:
            print(f"    · {name}　锚点：{anchor}　属性：{attr.value}")

        n = len(elements)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = elements[i], elements[j]
                state, bias = judge(a[2], b[2])
                bias_txt = f"　偏向：{bias}" if bias and bias != "无" else ""
                print(f"      {a[0]} × {b[0]}  →  {state.value}{bias_txt}"
                      f"　→ {POSITION[state.value]}")


def show_folding():
    """极 / 衰 折回基础三档 —— 这张表也是通用的，不含领域词。"""
    print("\n" + "=" * 74)
    print("  ② 极 / 衰 折回基础三档（同一套引擎，与领域无关）")
    print("=" * 74)
    for attr in A:
        base = base_of(attr)
        mark = "　← 折回" if base is not attr else ""
        print(f"    {attr.value:<4} → {base.value}{mark}")


def show_depth():
    """深浅：把档位移动一格。引擎里没有具体符号名，名单由领域层给。"""
    print("\n" + "=" * 74)
    print("  ③ 深浅：档位移动一格（引擎不含具体符号名）")
    print("=" * 74)
    for attr in (A.YIN, A.YANG, A.NEUTRAL):
        deep, weak = DEEPEN[attr], WEAKEN[attr]
        print(f"    {attr.value}　深 → {deep.value}（含义加「{DEPTH_PREFIX['深']}」）"
              f"　浅 → {weak.value}（含义加「{DEPTH_PREFIX['浅']}」）")
    print("\n    ⚠️ 引擎只提供「档位怎么动」；")
    print("       「哪些名字参与」由领域层决定 —— 那就是 engine/color_rules.py。")


def show_domain_layer():
    """领域层可以整个替换 —— 这个 demo 用的是【光/影·暖/冷】，不是颜色。"""
    import color_rules as domain

    print("\n" + "=" * 74)
    print("  ④ 领域层是可替换的：本仓库装的是【光/影 · 暖/冷】")
    print("=" * 74)
    print(f"    参与对立的符号：{sorted(domain.OPPOSITION_COLORS)}")
    print(f"    合法对立对数量：{len(domain.OPPOSITION_PAIRS)}")

    # ★ 层结构也来自领域：引擎默认是塔罗的四层，这里读的是本领域声明的三层
    import engine as eng
    same = tuple(domain.LAYERS) == tuple(eng.LAYERS)
    print(f"\n    领域声明的层结构：{tuple(domain.LAYERS)}")
    print(f"    引擎实际使用的层：{tuple(eng.LAYERS)}")
    print(f"    → {'一致 —— 层结构由领域决定，引擎只是读取' if same else '不一致（有问题）'}")

    cases = [
        ("光", "影", ["明亮"], ["暗淡"]),
        ("暖", "冷", ["聚拢"], ["散开"]),
        ("光", "暖", ["明亮"], ["聚拢"]),      # 不算对立对
    ]
    for a, b, ma, mb in cases:
        r = domain.resolve_opposition(a, b, ma, mb)
        if r is None:
            print(f"\n    {a} × {b}　→　不算合法对立对（返回 None）")
            continue
        print(f"\n    {a} × {b}　→　激烈程度：{r['intensity']}")
        print(f"        属性：{a} → {r['attr_a'].value if r['attr_a'] else '不变'}"
              f"　{b} → {r['attr_b'].value if r['attr_b'] else '不变'}")
        print(f"        含义：{a} → {r['meanings_a']}")
        print(f"        　　　{b} → {r['meanings_b']}")


def show_generality():
    """同一张 6 行表，换个输入 → 结论完全不同。"""
    print("\n" + "=" * 74)
    print("  ⑤ 同一张 6 行表，换个输入 → 结论完全不同")
    print("=" * 74)
    cases = [
        ("中 + 阳",   A.NEUTRAL,     A.YANG),
        ("中 + 阴",   A.NEUTRAL,     A.YIN),
        ("极阴 + 阳", A.EXTREME_YIN, A.YANG),   # 极阴折回阴 → 阴 + 阳
        ("衰阳 + 阳", A.DECAY_YANG,  A.YANG),   # 衰阳折回阳 → 阳 + 阳
    ]
    for label, a, b in cases:
        state, bias = judge(a, b)
        tail = f"（偏向 {bias}）" if bias and bias != "无" else ""
        print(f"    {label:<12} → {state.value}{tail}　→ {POSITION[state.value]}")


if __name__ == "__main__":
    print()
    show_pairing()
    show_folding()
    show_depth()
    show_domain_layer()
    show_generality()
    print("\n" + "=" * 74)
    print("  以上全部只用了一个通用引擎 + 一个可替换的领域层。")
    print("  没有完整字典、没有塔罗数据。")
    print("=" * 74)
    print()
