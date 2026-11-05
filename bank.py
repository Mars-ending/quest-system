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
            "3. 数值：构造病态数据（cond$(X)\approx 10^8$），正规方程 / QR / SVD 截断三种解法列相对误差，真值用高精度对照。",
            "4. 判决：半页——什么时候正规方程会炸、QR 为什么稳、SVD 截断在什么意义上已经不在解同一个问题。",
        ],
        "acceptance": "一份能跑的 py（numpy+mpmath），数值表必须真实跑出不是手填；推导写在 md；结尾三行复盘（卡点/我的假设/验证结果）。",
        "hours": "熟手研究生专注 5–6.5h，第 3 步占一半",
        "hints": [
            "L1 方向｜四问别平着做。先做 3（数值实验）：SVD 造病态 X（奇异值 logspace(0,-8)），真值用 mpmath 或大 λ 解析解对照。3 做完，1、2、4 会自己浮出一半。",
            "L2 洞察｜cond(X^T X) = cond(X)²——病态被平方放大；QR 不显式形成 X^T X，保持 cond(X)；SVD 硬截断解的是「另一个」问题（λ 软收缩 vs 硬截断——第 4 问题眼）。MAP：高斯似然取 -log 得最小二乘，高斯先验同理，目标 = 两项相加。",
            "L3 草稿｜data/hints/m1-l3-starter.py 是能跑的实验骨架（三种解法里法C留白给你），起步从这里抄。",
        ],


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
        "hints": [
            "L1 方向｜先写实现对拍（1 小时内），对拍过了再碰证明。证明卡住时去做第 3 问计时实验——退化现象会给你直觉：只有路径压缩是 O(log n)，不是 α(n)。",
            "L2 洞察｜按秩合并保「秩」不减（秩≠树高，压缩后秩只是上界）。证明主轴：k 秩节点至多 n/2^k 个（指数衰减）→ 按层汇聚 → O(log* n) → α(n)。别想一步写出 α。",
            "L3 草稿｜data/hints/a1-l3-starter.py：DSU 骨架 + 对拍占位（换成真暴力实现）+ 计时实验位置。",
        ],


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
        "hints": [
            "L1 方向｜先 LayerNorm 后 Dropout；自检是主体不是附带——写通用 gradcheck，以后每题复用。",
            "L2 洞察｜LayerNorm 沿特征维（每样本自己），BatchNorm 沿 batch 维——方向反了自检必炸。中心差分 (f(x+h)-f(x-h))/2h 用 float64；Dropout 反向必须用正向同一个 mask（缓存！），scale=1/(1-p) 放正向。",
            "L3 草稿｜data/hints/ai1-l3-starter.py：通用 num_grad + rel_err 骨架，留了实现位。",
        ],


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
        "hints": [
            "L1 方向｜第一遍只圈他实际给的东西（文末六条规则 + 反面例子）；第二遍才轮到不同意。摘要 400 词只能装 3 规则 + 2 诊断——选哪条本身就是考题。",
            "L2 洞察｜他的核心主张是「语言退化是思想退化的症状，且可自愈」——反驳打这个靶。可用角度：他自己违反自己的规则吗（找原文例证）/「意思明了就好」在数学写作成立吗/政治语言能靠文体改革治愈吗。挑一条写透。",
            "L3 草稿｜data/hints/e1-outline.md：五段结构模板，最后用他自己的六条规则检查你自己的稿。",
        ],


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
