# -*- coding: utf-8 -*-
"""Quest 网页扩展：把任务系统挂进一个已有的单文件 Python 门户。

门户要求（本项目 web/README.md 里的最小接口）：
  · http.server.BaseHTTPRequestHandler 子类，类名 H，已绑定 127.0.0.1
  · 已有函数：check_auth(header) -> bool、shell(title, body, active) -> str、
              esc(s)、parse_qs、urlparse、unquote、quote、json、re、os、time、
              subprocess、datetime
  集成方式：在门户文件的 `if __name__ == "__main__":` 之前 import 本块，
  或直接把本文件内容追加到门户源码里（见 web/README.md 的三种接法）。

页面：
  /quest          总览：当前任务全文 + 计时/交卷/调整/点评按钮 + 历史表
  /quest/timer    计时器（▶ / ⏸ / ⏹ 记账）
  /quest/do       动作入口（GET 开关计时与表单、POST 交卷与调整）
  /quest/eval/xx  点评存档查看

数据目录：QUEST_DATA（默认 ~/quest）；点评 agent 命令：QUEST_EVAL_CMD。
"""
import json
import os
import re
import subprocess
import time
from datetime import datetime
from urllib.parse import parse_qs, quote, unquote, urlparse

# ───────────────────────── 配置 ─────────────────────────

QUEST_DATA = os.environ.get("QUEST_DATA", os.path.join(os.path.expanduser("~"), "quest"))
QUEST_ENGINE = ["python3", os.path.join(QUEST_DATA, "engine.py")]
QUEST_EVAL_DIR = os.path.join(QUEST_DATA, "evals")
QUEST_TIMER = os.path.join(QUEST_DATA, "timer.json")
# 交卷后触发的点评命令。{prompt} 会被替换成完整 prompt（含题目块）。
# 任何 OpenAI 兼容 CLI agent 都能接，例如：
#   ["hermes", "-z", "{prompt}"]
#   ["python3", "my_eval_bot.py", "{prompt}"]
QUEST_EVAL_CMD = os.environ.get(
    "QUEST_EVAL_CMD",
    "hermes -z {prompt}").split()
QUEST_EVAL_TIMEOUT_S = 900
os.makedirs(QUEST_EVAL_DIR, exist_ok=True)

QUEST_EVAL_PROMPT = """你是任务验收人。请验收下面这道题的用户提交，并写评语。
规则：
1. 先跑代码再下结论：提交给了文件路径，用工具亲自查看并运行；跑不动就明确写「无法验证」，不要凭描述给结论。
2. 推导逐行核对；发现具体错误就指到行或公式。
3. 评语三段：站得住的部分 / 错漏与问题（具体位置）/ 下一题走哪条支、为什么。
4. 诚实优先：用时与产出体量明显不符要直接指出。
5. 最后登记结果：python3 {engine} set {qid} --state 完成 --review "<一句话总评>"；验收不合格则 --state 在架，评语以「退回：」开头。

题目与提交记录：
{block}
"""


# ───────────────────────── 引擎调用 ─────────────────────────

def _qrun(*args):
    r = subprocess.run(QUEST_ENGINE + list(args), capture_output=True,
                       text=True, timeout=60, cwd=QUEST_DATA)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _qstate():
    _, out = _qrun("state")
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return {}


def _qlive():
    """在架题原始块文本。"""
    try:
        with open(os.path.join(QUEST_DATA, "quest-log.md"), encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return None
    m = re.search(r"(## Q\d{3}[^\n]*\n(?:(?!## Q\d{3}).)*?- 状态[:：]\s*在架.*?)(?=\n## Q\d{3}|\Z)",
                  text, re.S)
    return m.group(1) if m else None


# ───────────────────────── 计时器 ─────────────────────────

def _timer_read():
    try:
        with open(QUEST_TIMER, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"op": "idle", "acc": 0, "since": None, "label": ""}


def _timer_write(d):
    with open(QUEST_TIMER, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)


def _timer_elapsed(d):
    if d.get("op") == "run" and d.get("since"):
        return d.get("acc", 0) + time.time() - d["since"]
    return d.get("acc", 0)


def _timer_book(d):
    """把当前累计时长记进账本头部「用户计时记录」。"""
    h = _timer_elapsed(d) / 3600.0
    row = "- %s | %s | %.2fh\n" % (datetime.now().strftime("%Y-%m-%d %H:%M"),
                                   d.get("label") or "未标注", h)
    path = os.path.join(QUEST_DATA, "quest-log.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    section = "## 用户计时记录\n\n"
    if section in text:
        text = text.replace(section, section + row, 1)
    elif "\n## Q" in text:
        text = text.replace("\n## Q", "\n" + section + row + "\n## Q", 1)
    else:
        text = text.rstrip() + "\n\n" + section + row
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    subprocess.run(["git", "add", "-A"], cwd=QUEST_DATA, timeout=15)
    subprocess.run(["git", "commit", "-qm", "timer book %.2fh %s" % (h, d.get("label", ""))],
                   cwd=QUEST_DATA, timeout=15, stderr=subprocess.DEVNULL)
    return h


# ───────────────────────── 点评 agent ─────────────────────────

def _eval_start(qid):
    block = _qlive() or "（账本里没抓到在架题原文，请直接读 %s 找 %s）" % (
        os.path.join(QUEST_DATA, "quest-log.md"), qid)
    prompt = QUEST_EVAL_PROMPT.format(qid=qid, block=block,
                                      engine=QUEST_ENGINE[-1])
    cmd = [c.replace("{prompt}", prompt) for c in QUEST_EVAL_CMD]
    out = os.path.join(QUEST_EVAL_DIR, "%s-%s.md" % (qid, datetime.now().date().isoformat()))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("> 评价生成中（%s 启动）…\n" % datetime.now().strftime("%H:%M:%S"))
    subprocess.Popen(cmd, stdout=open(out, "a", encoding="utf-8"),
                     stderr=subprocess.DEVNULL, start_new_session=True,
                     cwd=QUEST_DATA)
    return out


# ───────────────────────── 页面 ─────────────────────────

def _md_to_html(text):
    """迷你 Markdown：标题/列表/引用/代码围栏/粗斜体/行内码/链接/hr。
    公式 $..$ 原样保留（转义后是纯文本），交给页面上的 KaTeX auto-render。"""
    def _inline(x):
        x = x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        x = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", x)
        x = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", x)
        x = re.sub(r"`([^`]+)`", r"<code>\1</code>", x)
        x = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', x)
        return x

    out, para, code, buf = [], [], False, []
    _open_list = [None]
    lines = text.splitlines()

    def close_list():
        if _open_list[0]:
            out.append("</%s>" % _open_list[0])
            _open_list[0] = None

    def flush():
        if para:
            out.append("<p>%s</p>" % _inline(" ".join(para)))
            del para[:]

    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            flush()
            if not code:
                code = True
            else:
                out.append("<pre><code>%s</code></pre>"
                           % "".join(l.replace("&", "&amp;").replace("<", "&lt;")
                                     .replace(">", "&gt;") + "\n" for l in buf))
                buf, code = [], False
            i += 1
            continue
        if code:
            buf.append(ln)
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            flush()
            close_list()
            lv = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lv, _inline(m.group(2)), lv))
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", ln):
            flush()
            close_list()
            if not _open_list:
                out.append("<ul>")
                _open_list[0] = "ul"
            out.append("<li>%s</li>" % _inline(re.sub(r"^\s*[-*]\s+", "", ln)))
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if not re.match(r"^\s*[-*]\s+", nxt):
                close_list()
            i += 1
            continue
        if re.match(r"^\s*\d+[.)、]\s+", ln):
            flush()
            close_list()
            if not _open_list:
                out.append("<ol>")
                _open_list[0] = "ol"
            out.append("<li>%s</li>" % _inline(re.sub(r"^\s*\d+[.)、]\s+", "", ln)))
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if not re.match(r"^\s*\d+[.)、]\s+", nxt):
                close_list()
            i += 1
            continue
        if ln.strip() in ("---", "***", "___"):
            flush()
            close_list()
            out.append("<hr>")
            i += 1
            continue
        if ln.strip().startswith(">"):
            flush()
            close_list()
            out.append("<blockquote>%s</blockquote>" % _inline(ln.strip().lstrip(">").strip()))
            i += 1
            continue
        if not ln.strip():
            flush()
            i += 1
            continue  # 列表保持打开：允许编号项之间夹空行
        para.append(ln.strip())
        i += 1
    flush()
    close_list()
    if code and buf:
        out.append("<pre><code>%s</code></pre>"
                   % "".join(l.replace("&", "&amp;").replace("<", "&lt;")
                             .replace(">", "&gt;") + "\n" for l in buf))
    return "\n".join(out)


def _hints_panel(blk):
    """从题块解析 **提示** 段 → 逐层折叠面板。L1 摘要可见，L2/L3 点击展开。"""
    m = re.search(r"\*\*提示\*\*[^\n]*\n\n((?:- \*\*L\d.*?\n)+)", blk or "", re.S)
    if not m:
        return ""
    hints = re.findall(r"- \*\*(L\d[^*]*)\*\*(.*)", m.group(1))
    if not hints:
        return ""
    items = []
    for i, (head, body) in enumerate(hints):
        head = head.strip()
        body = body.strip()
        first = (i == 0)  # L1 默认展开
        items.append(
            '<details class="hint"%s><summary>%s</summary>'
            '<div class="hintbody">%s</div></details>'
            % (" open" if first else "",
               re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", esc(head[:70])),
               _md_to_html(body)))
    return ("<div class='hintwrap'><div class='hth'>💡 要提示吗？（先自己挣扎，一层不够再点下一层）</div>%s</div>"
            % "".join(items))

def _sublist(qid):
    """某题的提交物列表（带查看链接）。"""
    d = os.path.join(QUEST_HOME, "submissions", qid)
    if not os.path.isdir(d):
        return ""
    items = sorted(fn for fn in os.listdir(d) if not fn.startswith("."))
    if not items:
        return ""
    return "".join(
        '<li><a href="sub/%s/%s">%s</a> <small>(%sB)</small></li>'
        % (qid, quote(fn), esc(fn), os.path.getsize(os.path.join(d, fn)))
        for fn in items)

def _qpanel(full=True, qid=None):
    """题目面板：<details> 可折叠；full=False 时只显示摘要行。"""
    got = _qlive()
    blk = got[0] if isinstance(got, tuple) else got
    if not blk:
        return "<div class='qbox'><summary>❓ 题目</summary><div class='qmini'>当前没有在架任务</div></div>"
    qid = qid or blk.splitlines()[0].replace("## ", "").split(" · ")[0]
    # 摘要 = 标题行 + 前 2 步
    lines = [l for l in blk.splitlines() if l.strip()]
    title = lines[0].replace("## ", "")
    steps = [l for l in lines if re.match(r"^\d+\.", l.strip())]
    acc = next((l for l in lines if l.startswith("**验收**")), "")
    summ = esc(" · ".join(steps[0].strip()[:56].split("：", 1)[-1:] or [""])) if steps else ""
    # 题面渲染：去掉块级元信息行（## 标题 / 状态 / 域 / 前置 / 用时 / 答案 / 验收 / 评语 / 提示段）
    meta_pat = re.compile(
        r"^## Q\d{3}.*$|^\*\*题目\*\*.*$|^- 状态[:：].*$|^- 域/节点[:：].*$|^- 前置[:：].*$|"
        r"^- 用时[:：].*$|^- 答案[:：].*$|^- 验收[:：].*$|^- 评语[:：].*$|"
        r"^\*\*提示\*\*.*$", re.M)
    hints_m = re.search(r"\*\*提示\*\*[^\n]*\n\n(?:- \*\*L\d.*?\n)+", blk, re.S)
    body_md = meta_pat.sub("", blk)
    if hints_m:
        body_md = body_md.replace(hints_m.group(0), "")
    body_md = body_md.replace("**验收**：", "**验收**：").replace("**6h 口径**：", "**6h 口径**：").strip()
    full_html = _md_to_html(body_md) if full else ""
    extra = ("<div class='qmini'>↑ 完整题面（含验收与 6h 口径），做题时停在这页题目一直在<br>"
             "<a href='./'>← 返回任务页</a> · <a href='do?op=accept_form&q=%s'>📥 交卷</a></div>" % qid) if full else ""
    inner = (("<div class='qfull'>%s</div>" % full_html) if full else
             "<div class='qmini'>%s …</div>" % esc(steps[0].strip()[:60]) if steps else "")
    inner += _hints_panel(blk)
    acc_html = ("<div class='qmini'><b>验收：</b>%s</div>" % esc(acc.replace("**验收**：", ""))) if acc and not full else ""
    return ("<details class='qbox'%s><summary>%s</summary>%s%s%s</details>"
            % (" open" if full else "", esc(title), inner, acc_html, extra))

def _hints_panel(blk):
    """从题块解析 **提示** 段 → 逐层折叠面板。L1 摘要可见，L2/L3 点击展开。"""
    m = re.search(r"\*\*提示\*\*[^\n]*\n\n((?:- \*\*L\d.*?\n)+)", blk or "", re.S)
    if not m:
        return ""
    hints = re.findall(r"- \*\*(L\d[^*]*)\*\*(.*)", m.group(1))
    if not hints:
        return ""
    items = []
    for i, (head, body) in enumerate(hints):
        head = head.strip()
        body = body.strip()
        first = (i == 0)  # L1 默认展开
        items.append(
            '<details class="hint"%s><summary>%s</summary>'
            '<div class="hintbody">%s</div></details>'
            % (" open" if first else "",
               re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", esc(head[:70])),
               _md_to_html(body)))
    return ("<div class='hintwrap'><div class='hth'>💡 要提示吗？（先自己挣扎，一层不够再点下一层）</div>%s</div>"
            % "".join(items))


def _sublist(qid):
    """某题的提交物列表（带查看链接）。"""
    d = os.path.join(QUEST_HOME, "submissions", qid)
    if not os.path.isdir(d):
        return ""
    items = sorted(fn for fn in os.listdir(d) if not fn.startswith("."))
    if not items:
        return ""
    return "".join(
        '<li><a href="sub/%s/%s">%s</a> <small>(%sB)</small></li>'
        % (qid, quote(fn), esc(fn), os.path.getsize(os.path.join(d, fn)))
        for fn in items)


def _quest_check(self):
    if not check_auth(self.headers.get("Authorization")):
        self._unauth()
        return False
    return True


def _page_quest(msg=""):
    st = _qstate()
    live_block = _qlive()
    live_id = live_block.splitlines()[0].replace("## ", "").split(" · ")[0] if live_block else ""
    try:
        with open(os.path.join(QUEST_DATA, "quest-log.md"), encoding="utf-8") as f:
            text = f.read()
    except Exception:
        text = ""
    hist = ""
    for m in re.finditer(r"## (Q\d{3}) · ([^\n]+)\n- 状态[:：]\s*(\S+)"
                         r"(?:.*?域/节点[:：]\s*([^\n｜]+))?(?:.*?发出[:：]\s*(\S+))?"
                         r"(?:.*?用时[:：]\s*([^\n]+))?", text, re.S):
        qid, title, state, dom, issued, hours = [x.strip() if x else "" for x in m.groups()]
        color = {"完成": "#3a7", "已交·待验收": "#e80", "在架": "#08f",
                 "跳过": "#999", "看答案过关": "#a6a"}.get(state, "#999")
        hist += ("<tr><td><code>%s</code></td><td>%s</td><td style='color:%s'>%s</td>"
                 "<td>%s</td><td>%s</td><td>%s</td></tr>"
                 % (qid, esc(title[:40]), color, esc(state), esc(dom[:16]),
                    esc((issued or "")[:10]), esc(hours[:26])))
    if not hist:
        hist = "<tr><td colspan='6' class='empty'>账本为空</td></tr>"
    d = _timer_read()
    el = _timer_elapsed(d)
    tstat = "计时中 %.1fh（%s）" % (el / 3600.0, d.get("label") or "未标注") \
        if d.get("op") == "run" else ("暂停，累计 %.1fh" % (el / 3600.0) if el else "未计时")
    evals = ""
    try:
        for fn in sorted(os.listdir(QUEST_EVAL_DIR))[-3:][::-1]:
            evals += "<li><a href=\"eval/%s\">%s</a></li>" % (quote(fn), esc(fn))
    except Exception:
        pass
    body = """
<h1>Quest 任务系统</h1>
<div class="sub">账本与提交都在本机 git 里，每次操作留痕</div>
%s
<div class="panel"><h2>当前任务</h2>%s
<p>
 <a class="btn" href="do?op=timer_start&q=%s">▶ 开始/继续计时</a>
 <a class="btn" href="do?op=timer_pause&q=%s">⏸ 暂停</a>
 <a class="btn" href="do?op=timer_book&q=%s">⏹ 记账并停止</a>
 <a class="btn" href="do?op=accept_form&q=%s">📥 交卷</a>
 <a class="btn" href="do?op=adjust_form&q=%s">🔧 调整题目</a>
 <a class="btn" href="do?op=eval&q=%s">🔍 请求点评</a>
</p><div class="sub">计时状态：%s ｜ 完成 %d · 待验收 %d · 跳过 %d ｜ 累计记账 %d 条</div></div>
<div class="panel"><h2>任务历史</h2><table>
<tr><th>编号</th><th>题目</th><th>状态</th><th>域</th><th>发出</th><th>用时</th></tr>%s</table></div>
<div class="panel"><h2>最近点评</h2><ul>%s</ul></div>
""" % (("<div class='panel' style='border-color:#e80'><b>%s</b></div>" % esc(msg)) if msg else "",
       (_qpanel(full=True) if live_block
        else "<div class='qbox'><summary>❓ 题目</summary><div class='qmini'>当前没有在架任务</div></div>"),
       live_id, live_id, live_id, live_id, live_id, live_id, tstat,
       st.get("done", 0), st.get("pending", 0), st.get("skipped", 0), st.get("timer_lines", 0),
       hist, evals or "<li>暂无</li>")
    return shell("Quest · 每日任务", body, "quest", base="../")


def _page_timer():
    d = _timer_read()
    el = _timer_elapsed(d)
    status = "计时中" if d.get("op") == "run" else ("暂停" if el else "空闲")
    body = """
<h1>计时器</h1>
<div class="panel">
 <div class="k" style="font-size:14px">状态：%s ｜ 任务：%s</div>
 <div class="v" style="font-size:34px" id="clock">%s</div>
 <p>
  <a class="btn" href="do?op=timer_start&q=%s">▶ 开始/继续</a>
  <a class="btn" href="do?op=timer_pause">⏸ 暂停</a>
  <a class="btn" href="do?op=timer_book">⏹ 记账并停止</a>
 </p>
 <div class="empty">专注才计：去干别的先按暂停。记账写进账本头部。</div>
</div>
<script>
let base=%d, run=%s, t0=%s;
function fmt(s){s=Math.floor(s);return String(Math.floor(s/3600)).padStart(2,"0")+":"+String(Math.floor(s%%3600/60)).padStart(2,"0")+":"+String(s%%60).padStart(2,"0");}
function tick(){let v=base+(run?(Date.now()/1000-t0):0);document.getElementById("clock").textContent=fmt(v);}
setInterval(tick,1000);tick();
</script>
""" % (status, esc(d.get("label") or "未标注"), "%.2f h" % (el / 3600.0),
       d.get("label") or "", int(el),
       "true" if d.get("op") == "run" else "false", d.get("since") or 0)
    return shell("计时 · Quest", body, "quest", base="../")


def _page_form(kind, qid, err=""):
    e = "<div class='panel'><b>%s</b></div>" % esc(err) if err else ""
    if kind == "accept":
        body = e + """
<h1>交卷 · %s</h1>
<form method="post" action="do">
<input type="hidden" name="op" value="accept"><input type="hidden" name="q" value="%s">
<div class="panel">
 <p>专注用时（小时）<br><input name="hours" size="8" placeholder="5.5"></p>
 <p>提交文件（相对 submissions/，逗号分隔；可留空只用粘贴）<br>
    <input name="files" size="60" placeholder="q001/ridge.py,q001/notes.md"></p>
 <p>一句话说明<br><input name="note" size="60"></p>
 <p>直接粘贴文字/代码<br>
    <textarea name="paste" rows="8" style="width:95%%"></textarea></p>
 <p><button type="submit">登记交卷</button></p>
</div></form>""" % (esc(qid), esc(qid))
    elif kind == "adjust":
        body = e + """
<h1>调整题目 · %s</h1>
<form method="post" action="do">
<input type="hidden" name="op" value="adjust"><input type="hidden" name="q" value="%s">
<div class="panel">
 <p>方向<br><select name="dir">
   <option value="">（自由填写）</option>
   <option value="往数值方向扩展">往数值扩展</option>
   <option value="往概率/统计方向扩展">往概率/统计扩展</option>
   <option value="提高难度">提高难度</option>
   <option value="降低难度：给出更多提示">降低难度</option>
   <option value="结合另一个科目">跨科结合</option>
   <option value="这道题跳过，换一道等价的">跳过换题</option></select></p>
 <p>自由描述<br><input name="text" size="60"></p>
 <p><button type="submit">登记调整</button></p>
</div></form>""" % (esc(qid), esc(qid))
    else:
        body = "<h1>未知表单</h1>"
    return shell("Quest 表单", body, "quest", base="../")


# ───────────────────────── 路由钩子 ─────────────────────────
# 门户侧需要提供：check_auth / shell / esc / _unauth / _send / H（handler 类）
# 接法见 web/README.md；下面假设这些名字已存在。

def _q_redirect(self, to="./"):
    self.send_response(302)
    self.send_header("Location", to)
    self.send_header("Content-Length", "0")
    self.end_headers()


def _q_save_paste(qid, paste):
    d = os.path.join(QUEST_DATA, "submissions", qid)
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, "pasted-%s.txt" % datetime.now().strftime("%H%M%S"))
    with open(fp, "w", encoding="utf-8") as fh:
        fh.write(paste)
    return os.path.basename(fp)


def quest_route_GET(self, path, q):
    """门户 do_GET 里在自有路由之前调用；返回 True 表示已处理。"""
    if path != "/quest" and not path.startswith("/quest/"):
        return False
    if not check_auth(self.headers.get("Authorization")):
        self._unauth()
        return True
    if path == "/quest":
        _q_redirect(self, "quest/")
        return True
    if path == "/quest/":
        self._send(200, _page_quest(q.get("msg", [""])[0]).encode("utf-8"),
                   "text/html; charset=utf-8")
    elif path == "/quest/timer":
        self._send(200, _page_timer().encode("utf-8"), "text/html; charset=utf-8")
    elif path.startswith("/quest/eval/"):
        fn = os.path.basename(unquote(path[len("/quest/eval/"):]))
        real = os.path.realpath(os.path.join(QUEST_EVAL_DIR, fn))
        if not real.startswith(os.path.realpath(QUEST_EVAL_DIR)) or not os.path.isfile(real):
            self._send(404, shell("404", "没有这份点评", base="../").encode("utf-8"),
                       "text/html; charset=utf-8")
            return True
        with open(real, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        body = ("<h1>点评 · %s</h1><div class='panel'><pre style='white-space:pre-wrap;"
                "font-size:13px'>%s</pre></div><p><a href='../'>← 返回</a></p>"
                % (esc(fn), esc(txt[:40000])))
        self._send(200, shell("点评 · Quest", body, "quest", base="../").encode("utf-8"),
                   "text/html; charset=utf-8")
    elif path == "/quest/do":
        op = q.get("op", [""])[0]
        qid = q.get("q", [""])[0]
        if op.startswith("timer_"):
            d = _timer_read()
            if op == "timer_start":
                if d.get("op") != "run":
                    d = {"op": "run", "since": time.time(), "acc": d.get("acc", 0),
                         "label": qid or d.get("label", "")}
                    _timer_write(d)
                return _q_redirect(self, "timer")
            if op == "timer_pause":
                if d.get("op") == "run":
                    d["acc"] = _timer_elapsed(d)
                    d["op"] = "pause"
                    _timer_write(d)
                return _q_redirect(self, "timer")
            if op == "timer_book":
                if d.get("op") == "run":
                    d["acc"] = _timer_elapsed(d)
                    d["op"] = "pause"
                    _timer_write(d)
                if _timer_elapsed(d) > 60:
                    _timer_book(d)
                _timer_write({"op": "idle", "acc": 0, "since": None, "label": ""})
                return _q_redirect(self, "./?msg=" + quote("已记账并清零"))
            return _q_redirect(self, "timer")
        if op == "accept_form":
            self._send(200, _page_form("accept", qid).encode("utf-8"),
                       "text/html; charset=utf-8")
        elif op == "adjust_form":
            self._send(200, _page_form("adjust", qid).encode("utf-8"),
                       "text/html; charset=utf-8")
        elif op == "eval":
            if not qid:
                blk = _qlive()
                qid = blk.splitlines()[0].replace("## ", "").split(" · ")[0] if blk else ""
            if qid:
                _eval_start(qid)
                return _q_redirect(self, "./?msg=" +
                                   quote("点评已启动：agent 会先跑你的代码，约 2-5 分钟后刷新"))
            return _q_redirect(self, "./")
        else:
            return _q_redirect(self, "./")
    else:
        self._send(404, shell("404", "quest: 没有这个页面", base="../").encode("utf-8"),
                   "text/html; charset=utf-8")
    return True


def quest_route_POST(self, path):
    """门户 do_POST 里调用；返回 True 表示已处理。"""
    if path != "/quest/do":
        return False
    if not check_auth(self.headers.get("Authorization")):
        self._unauth()
        return True
    form = parse_qs(self.rfile.read(int(self.headers.get("Content-Length") or 0))
                    .decode("utf-8", "replace"))
    op = form.get("op", [""])[0]
    qid = form.get("q", [""])[0]
    if op == "accept":
        paste = (form.get("paste", [""])[0] or "").strip()
        saved = (" pasted-" + _q_save_paste(qid, paste)) if paste else ""
        files = (form.get("files", [""])[0] or "").strip()
        _, out = _qrun("accept", qid, "--hours", form.get("hours", [""])[0] or "?",
                       "--files", ("submissions/" + files if files else "") + saved,
                       "--note", form.get("note", [""])[0])
        ok = '"accepted"' in out
        subprocess.run(["git", "add", "-A"], cwd=QUEST_DATA, timeout=15)
        subprocess.run(["git", "commit", "-qm", "submission files %s" % qid],
                       cwd=QUEST_DATA, timeout=15, stderr=subprocess.DEVNULL)
        if ok:
            try:
                _eval_start(qid)
            except Exception:
                pass
            return _q_redirect(self, "./?msg=" + quote("交卷登记成功，点评已启动"))
        return _q_redirect(self, "./?msg=" + quote("登记失败：" + out[:200]))
    if op == "adjust":
        merged = "；".join(x for x in (form.get("dir", [""])[0].strip(),
                                      form.get("text", [""])[0].strip()) if x) or "（无内容）"
        _, out = _qrun("adjust", merged, qid or None)
        ok = '"adjust' in out
        return _q_redirect(self, "./?msg=" + quote("已登记调整" if ok else "调整失败：" + out[:200]))
    return _q_redirect(self, "./")
