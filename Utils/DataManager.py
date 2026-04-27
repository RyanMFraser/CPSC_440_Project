
import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"


def load_data(id):
    file_path = DATA_DIR / f"{id}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as json_file:
        payload = json.load(json_file)

    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object with 'id' and 'data' fields.")

    if payload.get("id") != id:
        raise ValueError(f"JSON id field mismatch: expected '{id}', found '{payload.get('id')}'.")

    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("JSON 'data' field must be an array of row objects.")

    return pd.DataFrame(rows)


def _validate_rows(data):
    if not isinstance(data, list):
        raise ValueError("data must be an array (list) of row objects.")

    if len(data) < 1:
        raise ValueError("data must contain at least one row.")

    required_fields = {"X", "Y", "Name", "Club"}
    for idx, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"Each row must be an object. Invalid row at index {idx}.")

        missing_fields = required_fields - set(row.keys())
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Row at index {idx} is missing required fields: {missing}")


def save_data(id, data, write_mode="overwrite"):
    if write_mode not in {"overwrite", "append"}:
        raise ValueError("write_mode must be either 'overwrite' or 'append'.")

    _validate_rows(data)

    final_rows = data

    file_path = DATA_DIR / f"{id}.json"
    if write_mode == "append" and file_path.exists():
        with file_path.open("r", encoding="utf-8") as json_file:
            existing_payload = json.load(json_file)

        if not isinstance(existing_payload, dict):
            raise ValueError("Existing JSON payload must be an object with 'id' and 'data' fields.")

        if existing_payload.get("id") != id:
            raise ValueError(
                f"Existing JSON id mismatch: expected '{id}', found '{existing_payload.get('id')}'."
            )

        existing_rows = existing_payload.get("data")
        if not isinstance(existing_rows, list):
            raise ValueError("Existing JSON 'data' field must be an array of row objects.")

        # Existing rows may predate stricter validation; validate before merging.
        _validate_rows(existing_rows)
        final_rows = existing_rows + data

    payload = {
        "id": id,
        "data": final_rows,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, indent=2)


