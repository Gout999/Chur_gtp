import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_entry(entry_path: Path, skill_name: str) -> None:
    result = subprocess.run(
        [sys.executable, str(entry_path), '{"action":"ping"}'],
        capture_output=True,
        text=True,
        check=False,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout.strip())
    assert payload["status"] == "not_implemented"
    assert payload["skill"] == skill_name


def test_all_teacher_skill_manifests_and_entries_are_runnable() -> None:
    expected = {
        "material_manager": {
            "skill_name": "material-manager",
            "tools": [
                "teacher_upload_material",
                "teacher_get_material_status",
                "teacher_adjust_boundary",
                "teacher_mark_importance",
                "teacher_get_knowledge_graph",
                "teacher_delete_material",
            ],
        },
        "monitor_dashboard": {
            "skill_name": "monitor-dashboard",
            "tools": [
                "teacher_get_class_overview",
                "teacher_get_student_detail",
                "teacher_get_student_cognition",
                "teacher_view_agent_logs",
                "teacher_query_interaction_history",
            ],
        },
        "intervene_console": {
            "skill_name": "intervene-console",
            "tools": [
                "teacher_get_escalations",
                "teacher_get_escalation_detail",
                "teacher_respond_to_escalation",
                "teacher_send_message",
                "teacher_pause_companion",
                "teacher_get_conversations",
            ],
        },
        "config_manager": {
            "skill_name": "config-manager",
            "tools": [
                "teacher_get_config",
                "teacher_update_config",
                "teacher_get_class_config",
                "teacher_update_class_config",
                "teacher_configure_notifications",
            ],
        },
        "lesson_plan_generator": {
            "skill_name": "lesson-plan-generator",
            "tools": [
                "generate_lesson_plan",
                "get_lesson_plan",
                "update_lesson_plan",
                "delete_lesson_plan",
                "generate_lesson_ppt",
                "get_ppt_status",
                "get_ppt_download",
                "get_ppt_preview",
                "list_lesson_plan_templates",
            ],
        },
    }

    for folder, cfg in expected.items():
        skill_dir = PROJECT_ROOT / "skills" / folder
        manifest = skill_dir / "skill.yaml"
        entry = skill_dir / "entry.py"
        assert manifest.exists(), f"missing manifest: {manifest}"
        assert entry.exists(), f"missing entry: {entry}"

        content = manifest.read_text(encoding="utf-8")
        assert f"name: {cfg['skill_name']}" in content
        for tool_name in cfg["tools"]:
            assert f"- {tool_name}" in content

        _run_entry(entry, cfg["skill_name"])
