#!/usr/bin/env bash
# quest-system 一键安装（目标机：Jetson / Pi 等 Debian 系 SBC，系统 python3 ≥ 3.8）
# 用法： bash scripts/install-jetson.sh
set -eu

DATA="${QUEST_HOME:-$HOME/quest}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> 数据目录：$DATA"
mkdir -p "$DATA/submissions" "$DATA/evals"

echo "==> 复制引擎与题库"
cp "$SRC/engine.py" "$SRC/bank.py" "$DATA/"
echo "==> 骨架账本（如已有账本则跳过，不动你的数据）"
if [ ! -f "$DATA/quest-log.md" ]; then
    cp "$SRC/data/quest-log.skeleton.md" "$DATA/quest-log.md"
fi
if [ ! -f "$DATA/quest-map.md" ]; then
    cp "$SRC/data/quest-map.skeleton.md" "$DATA/quest-map.md"
fi

echo "==> git 初始化（留痕）"
if [ ! -d "$DATA/.git" ]; then
    git -C "$DATA" init -q
fi
git -C "$DATA" add -A
git -C "$DATA" -c user.name="${USER:-quest}" -c user.email="${USER:-quest}@localhost" \
    commit -qm "quest: init" 2>/dev/null || echo "    (nothing to commit)"

echo "==> 冒烟测试"
python3 "$DATA/engine.py" state
echo "==> 完成。出第一题： python3 $DATA/engine.py issue"
echo "    网页接入： 见仓库 web/README.md（可选）"
echo "    哨兵 cron： 5 21 * * * cd $DATA && python3 $DATA/scripts/sentinel.py >> $DATA/sentinel.log 2>&1"
