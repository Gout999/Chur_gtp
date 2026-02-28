#!/usr/bin/env python3
"""
Companion 对话小测试 — 学生与 Companion 对话 + 清空记忆 + 快速测试。

用法（在 Chur_gtp 目录下）:
  python scripts/companion_chat_test.py           # 交互式对话（输入 clear 清空记忆，q 退出）
  python scripts/companion_chat_test.py --quick   # 只跑快速测试后退出

交互命令:
  clear / 清空 / 清空记忆  → 清空学生认知与交互记忆，重新开始
  q / quit / exit         → 退出

注意: 对话历史存在进程内存中。同一轮运行内的多轮对话会带上文；重新启动本脚本会清空历史，
因此“第二句没有第一句的上下文”若出现在重启后是预期行为。

依赖: 与 _demo_companion.py 相同。若报错 No module named 'arxiv'，可先 pip install arxiv
（或从仅含 Companion 的环境运行）。
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

# 脚本所在目录的上级 = Chur_gtp，加入 path 便于从任意位置运行
def _ensure_chur_gtp_in_path():
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)

# 与 demo 相同的 seed 与 state 结构
def _seed_authority():
    from memory.shared import shared_memory
    shared_memory.write("teacher_authority_graph", "global", {
        "scope_level": "moderate",
        "curriculum_topics": [
            "Newton's Second Law", "force", "momentum",
            "牛顿第二定律", "力", "动量",
        ],
        "knowledge_nodes": [
            {"concept": "Newton's Second Law", "description": "F=ma"},
            {"concept": "momentum", "description": "p=mv"},
            {"concept": "force", "description": "force concept"},
        ],
        "latest_boundary": {
            "scope_level": "moderate",
            "curriculum_topics": [
                "Newton's Second Law", "force", "momentum",
                "牛顿第二定律", "力", "动量",
            ],
        },
    })


def _clear_memory():
    """清空记忆：清空共享存储后重新写入教师知识边界，便于重新测试。"""
    from memory.shared import _STORE
    for ns in _STORE:
        _STORE[ns].clear()
    _seed_authority()
    print("[OK] 记忆已清空，可重新对话。\n")


def _one_turn(
    content: str,
    student_id: str = "test-student",
    target_concept: str = "牛顿第二定律",
    is_correct: bool | None = None,
    working_memory: dict | None = None,
):
    from agents.companion.node import socratic_companion_node

    state = {
        "event_type": "student_message",
        "event_payload": {
            "student_id": student_id,
            "content": content,
            "target_concept": target_concept,
            "is_correct": is_correct,
            "error_analysis": {},
            "time_spent": 0.0,
            "help_requests": 0,
        },
        "current_agent": "",
        "agent_decision": "",
        "tools_to_call": [],
        "working_memory": working_memory or {},
        "response_to_student": None,
        "response_to_teacher": None,
        "notifications": [],
        "session_id": "test-session",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "loop_count": 0,
    }
    result = socratic_companion_node(state)
    response = result.get("response_to_student", "")
    wm = result.get("working_memory", {})
    tools = result.get("tools_to_call", [])
    tool_names = [t.get("tool") for t in tools]
    next_wm = {"session_error_tracker": wm.get("session_error_tracker", {})}
    return response, tool_names, next_wm


def quick_tests():
    """快速测试：发送几条预设消息并打印回复。"""
    _seed_authority()
    student_id = "quick-test-student"
    wm = {}

    cases = [
        ("力不就是质量乘速度吗？", "牛顿第二定律", False, "❌ 误解: 力=质量×速度"),
        ("F=ma 对吧？", "牛顿第二定律", True, "✅ 正确: F=ma"),
        ("我放弃了，太难了", "牛顿第二定律", False, "😞 挫败"),
        ("动量p=mv，那力F是什么？", "force", False, "🔗 力与动量"),
    ]

    print("========== Companion 快速测试 ==========\n")
    for i, (content, concept, is_correct, label) in enumerate(cases, 1):
        print(f"--- [{i}] {label} ---")
        print(f"  学生: {content}")
        try:
            response, tools, wm = _one_turn(content, student_id, concept, is_correct, wm)
            print(f"  Companion: {response[:300]}{'…' if len(response) > 300 else ''}")
            print(f"  tools: {tools}")
        except Exception as e:
            print(f"  错误: {e}")
        print()
    print("========== 快速测试结束 ==========\n")


def interactive_loop():
    """交互式对话：输入消息回车发送，clear 清空记忆，q 退出。"""
    _seed_authority()
    student_id = "demo-student-001"
    wm = {}

    print("\n  Companion 对话测试（学生端）")
    print("  输入消息回车发送 | clear / 清空 = 清空记忆 | q = 退出\n")

    while True:
        try:
            line = input("你: ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line.lower() in ("q", "quit", "exit"):
            print("再见。\n")
            break
        if line.lower() in ("clear", "清空", "清空记忆", "reset"):
            _clear_memory()
            wm = {}
            continue

        print("Companion 思考中…")
        try:
            response, tools, wm = _one_turn(
                line,
                student_id=student_id,
                target_concept="牛顿第二定律",
                is_correct=None,
                working_memory=wm,
            )
            print(f"Companion: {response}")
            if tools:
                print(f"  [tools: {', '.join(tools)}]")
        except Exception as e:
            print(f"错误: {e}")
        print()


def main():
    _ensure_chur_gtp_in_path()
    parser = argparse.ArgumentParser(description="Companion 对话小测试")
    parser.add_argument("--quick", action="store_true", help="只跑快速测试后退出")
    args = parser.parse_args()

    try:
        if args.quick:
            quick_tests()
            return
        interactive_loop()
    except ImportError as e:
        print(f"导入失败: {e}", file=sys.stderr)
        print("请确保在 Chur_gtp 目录下运行，且依赖已安装（若缺 arxiv，可 pip install arxiv）。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
