# -*- coding: utf-8 -*-
"""用编造的数据在临时目录里做引擎冒烟测试（模拟 install + 一轮完整流程）。

跑法： python3 tests/smoke.py   （仓库根目录）
通过标准：全部 assert 过 + 最后打印 SMOKE_OK
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.basename(REPO) != "quest_repo" and not os.path.exists(os.path.join(REPO, "engine.py")):
    REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tests/ 在仓库根时的回退
ENGINE = os.path.join(REPO, "engine.py")


def run(args, data):
    env = dict(os.environ, QUEST_HOME=data)
    r = subprocess.run([sys.executable, ENGINE] + args,
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, "rc=%s out=%s err=%s" % (r.returncode, r.stdout, r.stderr)
    return r.stdout.strip()


def main():
    tmp = tempfile.mkdtemp(prefix="quest-smoke-")
    data = os.path.join(tmp, "quest")
    os.makedirs(data)
    # 骨架账本
    shutil.copy(os.path.join(REPO, "data", "quest-log.skeleton.md"),
                os.path.join(data, "quest-log.md"))

    # 1. 空账本 state
    st = json.loads(run(["state"], data))
    assert st["total"] == 0 and st["live"] == [], st

    # 2. 出第一题（M1）
    r = json.loads(run(["issue"], data))
    assert r["action"] == "issued" and r["id"] == "Q001", r
    st = json.loads(run(["state"], data))
    assert st["total"] == 1 and st["live"][0]["id"] == "Q001", st

    # 3. 在架时 issue 不出新题
    r = json.loads(run(["issue"], data))
    assert r["action"] == "exists" and r["id"] == "Q001", r
    st = json.loads(run(["state"], data))
    assert st["total"] == 1, st

    # 4. 交卷
    r = json.loads(run(["accept", "Q001", "--hours", "5.5",
                        "--files", "submissions/q001/a.py", "--note", "测试"], data))
    assert r["action"] == "accepted", r
    st = json.loads(run(["state"], data))
    assert st["pending"] == 1 and st["live"] == [], st
    log = open(os.path.join(data, "quest-log.md"), encoding="utf-8").read()
    assert "- 状态：已交·待验收" in log and "5.5 h" in log, log

    # 5. 验收：先退回
    r = json.loads(run(["set", "Q001", "在架", "退回：数值表没跑"], data))
    assert r["action"] == "set", r
    log = open(os.path.join(data, "quest-log.md"), encoding="utf-8").read()
    assert "退回：数值表没跑" in log, log

    # 6. 再交、再验收通过 → issue 出 A1
    run(["accept", "Q001", "--hours", "6.2", "--files", "submissions/q001/a.py"], data)
    r = json.loads(run(["set", "Q001", "完成", "四问全过"], data))
    assert r["action"] == "set", r
    st = json.loads(run(["state"], data))
    assert st["done"] == 1, st
    r = json.loads(run(["issue"], data))
    assert r["action"] == "issued" and r["id"] == "Q002", r
    log = open(os.path.join(data, "quest-log.md"), encoding="utf-8").read()
    assert "并查集" in log, log  # A1

    # 7. adjust：挂在头部（此时 Q002 在架，adjust 无参应并入在架题）
    r = json.loads(run(["adjust", "加一条对拍要求"], data))
    assert r["action"] == "adjusted" and r["id"] == "Q002", r
    log = open(os.path.join(data, "quest-log.md"), encoding="utf-8").read()
    assert "加一条对拍要求" in log, log

    # 8. 主干走完 → bank-empty
    for node in ("AI1", "E1"):  # A1 已由 issue 出（在架，手动判完成）
        pass
    run(["accept", "Q002", "--hours", "5.0"], data)
    run(["set", "Q002", "完成", "过"], data)
    run(["issue"], data)                       # AI1 → Q003
    run(["accept", "Q003", "--hours", "5.0"], data)
    run(["set", "Q003", "完成", "过"], data)
    run(["issue"], data)                       # E1 → Q004
    run(["accept", "Q004", "--hours", "4.0"], data)
    run(["set", "Q004", "完成", "过"], data)
    r = json.loads(run(["issue"], data))
    assert r["action"] == "bank-empty", r
    st = json.loads(run(["state"], data))
    assert st["done"] == 4, st

    shutil.rmtree(tmp, ignore_errors=True)
    print("SMOKE_OK")


if __name__ == "__main__":
    main()
