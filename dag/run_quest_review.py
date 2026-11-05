# -*- coding: utf-8 -*-
"""quest-review DAG runner：任务题号作参数，从 stdin 读草稿。"""
import sys
from chatdev import run_workflow

yaml_file = "/home/wei/quest-dag/quest-review.yaml"
task_prompt = sys.stdin.read()
result = run_workflow(yaml_file=yaml_file, task_prompt=task_prompt)
print("SUCCESS:", result.success)
fm = result.final_message
print("=== FINAL ===")
print(fm if isinstance(fm, str) else str(fm))
