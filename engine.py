#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quest engine —— 每日任务系统的核心逻辑。

账本 = quest-log.md（唯一真实源，git 管历史）；脉络 = quest-map.md。
职责：在架判定、按脉络出题、交卷登记、用户调整登记、状态汇总。
不负责：验收与评语（评价 agent 的活）、网页渲染（门户的活）。

用法：
  python3 engine.py state                    # 汇总 JSON（在架题、统计）
  python3 engine.py issue                    # 无在架则按脉络出下一题
  python3 engine.py accept Q00x --hours 5.5 --files a.py --note 摘要
  python3 engine.py adjust "想偏向数值方向" [Q00x]
  python3 engine.py set Q00x --state 完成 --review "评语..."

环境变量：
  QUEST_HOME   数据目录（默认 ~/quest）
  QUEST_BANK   题库模块（默认 engine.bank；见 bank.w0）
"""
import importlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOME = os.environ.get("QUEST_HOME", os.path.expanduser("~/quest"))
LOG = os.path.join(HOME, "quest-log.md")
BANK_NAME = os.environ.get("QUEST_BANK", "bank")
STATES = ("在架", "已交·待验收", "完成", "跳过", "看答案过关")


# ───────────────────────── 账本解析 ─────────────────────────

def read_log():
    with open(LOG, encoding="utf-8") as f:
        return f.read()


def blocks(text):
    """拆账本：返回 (头部文本, [任务块])。任务块 = ## Q### 开头的段。"""
    parts = re.split(r"\n(?=## Q\d{3})", text)
    head, items = parts[0], []
    for p in parts[1:]:
        p = p.rstrip() + "\n"
        m = re.match(r"## (Q\d{3}) · (.+)", p)
        if not m:
            continue
        st = re.search(r"- 状态[:：]\s*(\S+)", p)
        dn = re.search(r"- 域/节点[:：]\s*(.+?)(?:｜发出[:：]\s*(\S+))?\s*$", p, re.M)
        items.append({"id": m.group(1), "title": m.group(2).strip(),
                      "state": st.group(1) if st else "?",
                      "dom": dn.group(1).strip() if dn else "",
                      "issued": dn.group(2) if (dn and dn.group(2)) else "",
                      "raw": p})
    return head, items


def write_log(head, items):
    with open(LOG, "w", encoding="utf-8") as f:
        f.write(head.rstrip() + "\n\n")
        for it in items:
            f.write("\n" + it["raw"].rstrip() + "\n")


def git_snap(msg):
    """账本每次变更都留一个 git 提交（无仓库时静默跳过）。"""
    try:
        subprocess.run(["git", "add", "-A"], cwd=HOME, timeout=15)
        subprocess.run(["git", "commit", "-qm", msg], cwd=HOME, timeout=15,
                       stderr=subprocess.DEVNULL)
    except Exception:
        pass


def bank():
    """题库模块：提供 next_task(items) -> dict 或 None。"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    return importlib.import_module(BANK_NAME)


# ───────────────────────── 出题 ─────────────────────────

def make_block(qid, task):
    """task = {dom, title, steps[], acceptance, hours, prev} → 账本块文本。"""
    today = date.today().isoformat()
    steps = "\n".join(task["steps"])
    return ("## %s · %s\n\n- 状态：在架\n- 域/节点：%s｜发出：%s\n- 前置：%s\n\n"
            "**题目**\n\n背景与做法：\n\n%s\n\n**验收**：%s\n**6h 口径**：%s\n\n"
            "- 用时：__\n- 答案：__\n- 验收：__\n- 评语：__\n"
            % (qid, task["title"], task["dom"], today, task.get("prev", "无"),
               steps, task["acceptance"], task["hours"]))


def next_qid(used):
    return next("Q%03d" % i for i in range(1, 1000) if ("Q%03d" % i) not in used)


def cmd_issue():
    head, items = blocks(read_log())
    live = [it for it in items if it["state"] == "在架"]
    if live:
        it = live[0]
        days = None
        if it["issued"]:
            days = (date.today() - datetime.strptime(it["issued"], "%Y-%m-%d").date()).days
        print(json.dumps({"action": "exists", "id": it["id"], "title": it["title"],
                          "dom": it["dom"], "issued": it["issued"], "days": days},
                         ensure_ascii=False))
        return
    # 账本头部若挂了「下次出题调整」，随题并入并用掉
    adj = re.search(r"## 下次出题调整\n\n(.+?)\n\n", head, re.S)
    instructions = adj.group(1).strip() if adj else ""
    qid = next_qid({it["id"] for it in items})
    task = bank().next_task(items)
    if task is None:
        print(json.dumps({"action": "bank-empty"}, ensure_ascii=False))
        return
    new = make_block(qid, task)
    note = task.get("note", task["dom"])
    if adj:
        head = head.replace(adj.group(0), "")
        new = new.replace("**题目**\n", "**用户调整（出题时生效）**：%s\n\n**题目**\n" % instructions)
        note += "＋用户调整已并入"
    write_log(head, items + [{"id": qid, "title": "", "state": "在架",
                              "dom": "", "issued": "", "raw": new}])
    git_snap("issue %s %s" % (qid, note))
    print(json.dumps({"action": "issued", "id": qid, "note": note}, ensure_ascii=False))


# ───────────────────────── 交卷 / 调整 / 状态 ─────────────────────────

def find(items, qid):
    for it in items:
        if it["id"] == qid:
            return it
    raise SystemExit("没找到 %s" % qid)


def cmd_accept(args):
    head, items = blocks(read_log())
    it = find(items, args["qid"])
    raw = it["raw"]
    raw = raw.replace("- 用时：__",
                      "- 用时：%s h（交于 %s）" % (args.get("hours", "?"), date.today().isoformat()), 1)
    files, note = args.get("files", ""), args.get("note", "")
    raw = raw.replace("- 答案：__", "- 答案：%s%s" % (files, ("｜" + note) if note else ""), 1)
    raw = re.sub(r"- 状态[:：]\s*在架", "- 状态：已交·待验收", raw, count=1)
    it["raw"], it["state"] = raw, "已交·待验收"
    write_log(head, items)
    git_snap("accept %s (%sh)" % (args["qid"], args.get("hours", "?")))
    print(json.dumps({"action": "accepted", "id": args["qid"]}, ensure_ascii=False))


def cmd_adjust(text, qid=None):
    head, items = blocks(read_log())
    live = [it for it in items if it["state"] == "在架"]
    stamp = date.today().isoformat()
    if qid:
        it = find(items, qid)
    elif live:
        it = live[0]
    else:  # 没有在架题 → 挂到头部，下次出题时生效
        head = head.rstrip() + "\n\n## 下次出题调整\n\n%s（%s）\n\n" % (text, stamp)
        write_log(head, items)
        git_snap("adjust-next")
        print(json.dumps({"action": "queued-for-next", "text": text}, ensure_ascii=False))
        return
    it["raw"] = it["raw"].replace("**题目**\n",
                                  "**用户调整（%s）**：%s\n\n**题目**\n" % (stamp, text), 1)
    write_log(head, items)
    git_snap("adjust %s" % it["id"])
    print(json.dumps({"action": "adjusted", "id": it["id"]}, ensure_ascii=False))


def cmd_set(qid, state, review=None):
    if state not in STATES:
        raise SystemExit("状态必须是 %s 之一" % "/".join(STATES))
    head, items = blocks(read_log())
    it = find(items, qid)
    raw = re.sub(r"- 状态[:：]\s*\S+", "- 状态：%s" % state, it["raw"], count=1)
    if review:
        if "- 评语：__" in raw:
            raw = raw.replace("- 评语：__", "- 评语：%s（%s）" % (review, date.today().isoformat()), 1)
        else:  # 退回重做可能有旧评语，追加不覆盖
            raw = raw.replace("- 评语：", "- 评语：%s（%s）｜再评：" % (review, date.today().isoformat()), 1)
    it["raw"], it["state"] = raw, state
    write_log(head, items)
    git_snap("set %s -> %s" % (qid, state))
    print(json.dumps({"action": "set", "id": qid, "state": state}, ensure_ascii=False))


def cmd_state():
    head, items = blocks(read_log())
    live = [it for it in items if it["state"] == "在架"]
    out = {"live": [{"id": it["id"], "title": it["title"], "dom": it["dom"],
                     "issued": it["issued"]} for it in live],
           "done": sum(1 for it in items if it["state"] in ("完成", "看答案过关")),
           "skipped": sum(1 for it in items if it["state"] == "跳过"),
           "pending": sum(1 for it in items if it["state"] == "已交·待验收"),
           "total": len(items)}
    m = re.search(r"## 用户计时记录\n\n(.*?)(?=\n## |\Z)", head, re.S)
    out["timer_lines"] = len(m.group(1).strip().splitlines()) if m and m.group(1).strip() else 0
    print(json.dumps(out, ensure_ascii=False))


# ───────────────────────── CLI ─────────────────────────

def main():
    a = sys.argv[1:]
    if not a or a[0] == "state":
        return cmd_state()
    cmd = a[0]
    if cmd == "issue":
        return cmd_issue()
    if cmd == "accept":
        rest = a[1:]
        d = {"qid": rest[0]}
        for i, x in enumerate(rest):
            if x == "--hours":
                d["hours"] = rest[i + 1]
            elif x == "--files":
                d["files"] = rest[i + 1]
            elif x == "--note":
                d["note"] = rest[i + 1]
        return cmd_accept(d)
    if cmd == "adjust":
        return cmd_adjust(a[1], a[2] if len(a) > 2 else None)
    if cmd == "set":
        return cmd_set(a[1], a[2], a[3] if len(a) > 3 else None)
    raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
