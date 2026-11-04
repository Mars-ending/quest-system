#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quest 哨兵壳：每晚 cron 触发，组装 prompt 交给点评/出题 agent。

配置（环境变量）：
  QUEST_DATA           数据目录（默认 ~/quest）
  QUEST_SENTINEL_CMD   agent 命令，{prompt} 会被替换（默认 "hermes -z {prompt}"）
输出：agent 的回复落 stdout（cron 里重定向进 sentinel.log）。
"""
import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DATA = os.environ.get("QUEST_DATA", str(Path.home() / "quest"))
ENGINE = os.path.join(DATA, "engine.py")

TEMPLATE = Path(__file__).resolve().parent.parent / "agent" / "sentinel-prompt.txt"


def main():
    prompt = TEMPLATE.read_text(encoding="utf-8").format(engine=ENGINE)
    cmd = os.environ.get("QUEST_SENTINEL_CMD", "hermes -z {prompt}").split()
    cmd = [c.replace("{prompt}", prompt) for c in cmd]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=3600, cwd=DATA)
    sys.stdout.write(r.stdout.decode("utf-8", "replace"))


if __name__ == "__main__":
    main()
