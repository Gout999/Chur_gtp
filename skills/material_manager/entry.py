"""Entrypoint for material-manager skill."""
import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="material-manager skill entrypoint")
    parser.add_argument("args", nargs="?", default="{}")
    parsed = parser.parse_args()

    try:
        payload = json.loads(parsed.args) if parsed.args else {}
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2

    print(
        json.dumps(
            {
                "status": "not_implemented",
                "skill": "material-manager",
                "received_args": payload,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
