# Teacher Skills

This directory contains teacher-side skill manifests and entry scripts.

Each skill folder includes:
- `skill.yaml`: skill metadata, exposed tools, and runtime command.
- `entry.py`: callable entrypoint used by the skill runner.

Current skills:
- `material_manager`
- `monitor_dashboard`
- `intervene_console`
- `config_manager`
- `lesson_plan_generator`

## Prompt-based skills

These skills use an instruction manifest rather than a Python entrypoint:

- `grill-me` — a relentless interview to sharpen a plan or design.
