import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ci_utils import build_export_payload, parse_ci_notes


INVENTORY_DIR = Path.cwd() / "data"
INVENTORY_PATH = INVENTORY_DIR / "inventory.json"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_inventory_file() -> None:
    INVENTORY_DIR.mkdir(exist_ok=True)
    if not INVENTORY_PATH.exists():
        INVENTORY_PATH.write_text(json.dumps({"records": []}, indent=2), encoding="utf-8")


def load_records() -> List[Dict[str, Any]]:
    ensure_inventory_file()
    payload = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    return sorted(records, key=lambda item: item.get("updated_at", ""), reverse=True)


def save_records(records: List[Dict[str, Any]]) -> None:
    ensure_inventory_file()
    INVENTORY_PATH.write_text(json.dumps({"records": records}, indent=2), encoding="utf-8")


def get_record(record_id: str) -> Optional[Dict[str, Any]]:
    for record in load_records():
        if record.get("id") == record_id:
            return record
    return None


def create_ci_submission(notes: str, user: Dict[str, str]) -> Dict[str, Any]:
    parsed = parse_ci_notes(notes)
    payload = build_export_payload(parsed)
    created_at = now_iso()
    record = {
        "id": uuid4().hex[:10].upper(),
        "status": "submitted_to_ao",
        "template_key": "",
        "template_label": "",
        "ci_notes": notes.strip(),
        "parsed_data": parsed,
        "account_name": parsed.get("account_name", ""),
        "applicant_name": payload.get("applicant_name", ""),
        "ci_submitter_email": user.get("email", ""),
        "ci_submitter_name": user.get("name", "CI User"),
        "ci_submitted_at": created_at,
        "ao_email": "",
        "ao_name": "",
        "ao_generated_at": "",
        "submitted_to_officer_at": "",
        "generated_file_name": "",
        "generated_file_path": "",
        "officer_note": "",
        "created_at": created_at,
        "updated_at": created_at,
    }
    records = load_records()
    records.append(record)
    save_records(records)
    return record


def update_record(record_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    records = load_records()
    updated_record: Optional[Dict[str, Any]] = None
    for index, record in enumerate(records):
        if record.get("id") != record_id:
            continue
        merged = dict(record)
        merged.update(updates)
        merged["updated_at"] = now_iso()
        records[index] = merged
        updated_record = merged
        break

    if updated_record is None:
        return None

    save_records(records)
    return updated_record


def list_records_by_status(statuses: List[str]) -> List[Dict[str, Any]]:
    wanted = set(statuses)
    return [record for record in load_records() if record.get("status") in wanted]


def list_records_for_user(role: str, email: str) -> List[Dict[str, Any]]:
    email = (email or "").lower()
    records = load_records()
    if role == "ci":
        return [record for record in records if record.get("ci_submitter_email", "").lower() == email]
    if role == "ao":
        return [record for record in records if record.get("status") in {"submitted_to_ao", "generated_by_ao", "submitted_to_officer"}]
    if role == "officer":
        return [record for record in records if record.get("status") == "submitted_to_officer"]
    return records
