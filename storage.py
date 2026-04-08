import json
from typing import Any


def ensure_file(path, default_data: Any) -> None:
    if not path.exists():
        path.write_text(json.dumps(default_data, indent=2), encoding="utf-8")


def load_json(path, default_data: Any) -> Any:
    ensure_file(path, default_data)
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def log_session_turn(session_log_file, turn: dict) -> None:
    session_log = load_json(session_log_file, [])
    session_log.append(turn)
    save_json(session_log_file, session_log)