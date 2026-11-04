# -*- coding: utf-8 -*-
"""题库模块：把「下一道题」从引擎里拆出来，换题库不动引擎。

接口只有一个：next_task(items) -> dict | None
  items   账本里已有的任务块（含 state/dom），用来判断进度与避免重复
  返回    {dom, title, steps[], acceptance, hours, prev?, note?} 或 None（题库发完）

`w0()` 给出主干四题；`next_task` 先走完主干，再按用户自己的 quest-map 展开。
把你的题目写进 quest-map.md 后，改这里的 W1 部分即可——引擎零改动。
"""

# ───────────────────────── W0 主干（可对拍的四题） ─────────────────────────

W0 = {
    "M1": {
        "dom": "数学 / M1（W0 主干）",
        "title": "岭回归的四种面目",
        "steps": [
            "1. 几何：把 min‖y−Xw‖²+λ‖w‖² 的解写成投影形式，说明 λ 改变的是往哪个子空间投影（手推，含闭式解）。",
            "2. 贝叶斯：证明它 = 高斯噪声+高斯先验的 MAP；写出后验均值与 MAP 重合的那一行。",
            "3. 数值：构造病态数据（cond(X)≈1e8），正规方程 / QR / SVD 截断三种解法列相对误差，真值用高精度对照。",
            "4. 判决：半页——什么时候正规方程会炸、QR 为什么稳、SVD 截断在什么意义上已经不在解同一个问题。",
        ],
        "acceptance": "一份能跑的 py（numpy+mpmath），数值表必须真实跑出不是手填；推导写在 md；结尾三行复盘（卡点/我的假设/验证结果）。",
        "hours": "熟手研究生专注 5–6.5h，第 3 步占一半",
        "note": "（W0 主干 1/4）",
    },
    "A1": {
        "dom": "算法·代码 / A1（W0 主干）",
        "title": "并查集的摊还账",
        "steps": [
            "1. 单文件实现并查集（路径压缩+按秩合并），与暴力连通性对拍（随机数据 ≥1e5 操作）。",
            "2. 纸上摊还分析：证明带路径压缩+按秩合并的均摊复杂度 O(α(n))（Ackermann 反函数）。",
            "3. 实测退化：去掉按秩合并，量同一批数据的总耗时变化，解释现象。",
        ],
        "acceptance": "代码 + 证明 + 两组实测数。",
        "hours": "熟手研究生专注 4–6h，证明部分至少 1.5h",
        "note": "（W0 主干 2/4）",
    },
    "AI1": {
        "dom": "人工智能 / AI1（W0 主干）",
        "title": "LayerNorm + Dropout 手撕",
        "steps": [
            "1. 纯 numpy 实现 LayerNorm 与 Dropout（训练/推理两种模式）。",
            "2. 数值梯度自检：float64 中心差分，所有参数相对误差 < 1e-6。",
            "3. 实验：同一小任务上有/无 Dropout 的训练曲线各一条，说明推理模式行为差异。",
        ],
        "acceptance": "py + 自检通过输出 + 两条曲线数据。",
        "hours": "熟手研究生专注 4–6h",
        "note": "（W0 主干 3/4）",
    },
    "E1": {
        "dom": "英语 / E1（W0 主干）",
        "title": "Orwell《Politics and the English Language》精读",
        "steps": [
            "1. 全文精读（公版，Project Gutenberg 可下）。",
            "2. 400 词英文摘要：只写他真正主张的三条规则与两条诊断。",
            "3. 3 处「我不同意」，每处给理由（英文）。",
        ],
        "acceptance": "一篇英文稿（摘要+反驳），按可读性检查表评。",
        "hours": "熟手研究生专注 3–5h",
        "note": "（W0 主干 4/4）",
    },
}
W0_ORDER = ["M1", "A1", "AI1", "E1"]


def _w0_done(items):
    """已通过的 W0 节点集合。"""
    done = set()
    for it in items:
        if it["state"] in ("完成", "看答案过关") and "W0" in it["dom"]:
            m = re_search(r"/ (M\d|A\d|AI\d|E\d)", it["dom"])
            if m:
                done.add(m.group(1))
    return done


def re_search(pat, s):
    import re
    m = re.search(pat, s)
    return m


# ───────────────────────── 主入口 ─────────────────────────

def next_task(items):
    """返回下一道题；主干走完后返回 None（由你自己的 quest-map 接管）。"""
    done = _w0_done(items)
    for k in W0_ORDER:
        if k not in done:
            return dict(W0[k])
    # ── W1 及以后：在这里接你自己的脉络 ──
    # 例：
    # if "M1" in done and not any("M2" in it["dom"] for it in items):
    #     return {...}
    return None
