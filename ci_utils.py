import re
from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

from openpyxl import load_workbook


TEMPLATE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "bpi": {
        "label": "BPI PDRN",
        "path": Path(r"C:\Users\Jan\Downloads\PDRN-MAPPING-1_efa98837-83fc-4d76-987a-3101659aafce.xls"),
        "sheet_name": "PDRN",
    },
    "maybank": {
        "label": "Maybank PDRN",
        "path": Path(r"C:\Users\Jan\Downloads\MAYBANK-PDRN_49cb9e3d-7f16-48f8-9d3f-4acb6e339d34.xlsx"),
        "sheet_name": "Sheet1",
    },
}

DEFAULT_TEMPLATE_KEY = "bpi"
DEFAULT_TEMPLATE_PATH = TEMPLATE_DEFINITIONS[DEFAULT_TEMPLATE_KEY]["path"]


CI_FORM_DEFAULTS: Dict[str, Any] = {
    "reference_number": "",
    "bpi_request_number": "",
    "los_request_number": "",
    "account_name": "",
    "subject_last_name": "",
    "subject_first_name": "",
    "subject_middle_name": "",
    "subject_nickname": "",
    "subject_bday_age": "",
    "subject_birthplace": "",
    "subject_civil_status": "",
    "subject_gender": "",
    "subject_nationality": "",
    "subject_education": "",
    "subject_employment": "",
    "subject_business": "",
    "spouse_last_name": "",
    "spouse_first_name": "",
    "spouse_middle_name": "",
    "spouse_nickname": "",
    "spouse_bday_age": "",
    "spouse_birthplace": "",
    "spouse_civil_status": "",
    "spouse_gender": "",
    "spouse_nationality": "",
    "spouse_education": "",
    "spouse_employment": "",
    "spouse_business": "",
    "dependents": "",
    "complete_address": "",
    "present_address": "",
    "previous_address": "",
    "province": "",
    "region": "",
    "contact_number": "",
    "length_of_stay": "",
    "ownership": "",
    "vehicles": "",
    "type_of_residence": "",
    "no_of_storey": "",
    "classification": "",
    "house_condition": "",
    "made_of": "",
    "appearance": "",
    "accessibility": "",
    "neighborhood": "",
    "house_color": "",
    "gate_color": "",
    "fence_color": "",
    "interior": "",
    "exterior": "",
    "parking": "",
    "lot_area": "",
    "floor_area": "",
    "landmark": "",
    "corner": "",
    "time_of_visit": "",
    "nearest_bdo_branch": "",
    "bdo_distance": "",
    "utility_bills": "",
    "coordinates": "",
    "ownership_verification": "",
    "basis_of_ownership_verification": "",
    "living_condition": "",
    "neighborhood_classification": "",
    "area_definition": "",
    "adverse_finding": "",
    "remarks": "",
    "informants": "",
    "main_informant": "",
    "field_investigator": "",
    "requesting_officer": "",
    "date_time_inspected": "",
    "submitted_date": "",
    "submitted_time": "",
    "outcome": "",
    "raw_notes": "",
}


DIRECT_FIELD_MAP = {
    "ACCOUNT NAME": "account_name",
    "BDAY AGE": "subject_bday_age",
    "BIRTHPLACE": "subject_birthplace",
    "CIVIL STATUS": "subject_civil_status",
    "NATIONALITY": "subject_nationality",
    "EDUCATIONAL ATTAINMENT": "subject_education",
    "EMPLOYMENT": "subject_employment",
    "BUSINESS": "subject_business",
    "COMPLETE ADDRESS": "complete_address",
    "PRESENT ADDRESS": "present_address",
    "LENGTH OF STAY": "length_of_stay",
    "PREVIOUS": "previous_address",
    "PROVINCE": "province",
    "CONTACT NUMBER": "contact_number",
    "OWNERSHIP": "ownership",
    "VEHICLES": "vehicles",
    "TYPE OF RESIDENCE": "type_of_residence",
    "NO OF STOREY": "no_of_storey",
    "CLASSIFICATION": "classification",
    "HOUSE CONDITION": "house_condition",
    "MADE": "made_of",
    "APPEARANCE": "appearance",
    "ACCESSIBILITY": "accessibility",
    "NEIGHBORHOOD": "neighborhood",
    "HOUSE COLOR": "house_color",
    "GATE COLOR": "gate_color",
    "FENCE COLOR": "fence_color",
    "INTERIOR": "interior",
    "EXTERIOR": "exterior",
    "PARKING": "parking",
    "LOT AREA": "lot_area",
    "FLOOR AREA": "floor_area",
    "LANDMARK": "landmark",
    "CORNER": "corner",
    "TIME OF VISIT": "time_of_visit",
    "NEAREST BDO BRANCH": "nearest_bdo_branch",
    "KILOMETERS METERS AWAY": "bdo_distance",
}


PERSON_FIELD_MAP = {
    "LAST NAME": "last_name",
    "FIRST NAME": "first_name",
    "MIDDLE NAME": "middle_name",
    "NICKNAME": "nickname",
    "BDAY AGE": "bday_age",
    "BIRTHPLACE": "birthplace",
    "CIVIL STATUS": "civil_status",
    "NATIONALITY": "nationality",
    "EDUCATIONAL ATTAINMENT": "education",
}


SECTION_TOKENS = {
    "NAME OF SUBJECT": "subject",
    "NAME OF SPOUSE LIVE IN PARTNER": "spouse",
}


def normalize_label(value: str) -> str:
    cleaned = re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()
    return re.sub(r"\s+", " ", cleaned)


def compact_value(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\n", " ")).strip()


def join_name(last_name: str, first_name: str, middle_name: str) -> str:
    last_name = compact_value(last_name)
    first_name = compact_value(first_name)
    middle_name = compact_value(middle_name)
    first_part = " ".join(part for part in [first_name, middle_name] if part)
    if last_name and first_part:
        return f"{last_name}, {first_part}"
    return compact_value(" ".join(part for part in [last_name, first_name, middle_name] if part))


def split_address(address: str) -> Dict[str, str]:
    raw = compact_value(address)
    result = {
        "address_line_1": raw,
        "address_line_2": "",
        "address_line_3": "",
        "barangay": "",
        "city": "",
        "region": "",
    }
    if not raw:
        return result

    city_match = re.search(r"\b([A-Z ]+CITY)\b", raw.upper())
    if city_match:
        result["city"] = city_match.group(1).title()

    barangay_match = re.search(r"\b(BRGY\.?\s+[A-Z0-9 ]+?)(?=\s+[A-Z ]+CITY|$)", raw.upper())
    if barangay_match:
        result["barangay"] = compact_value(barangay_match.group(1).replace("BRGY.", "BRGY"))

    street_part = raw
    if result["barangay"]:
        street_part = re.split(r"\bBRGY\.?\b", raw, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    elif result["city"]:
        street_part = raw[: raw.upper().find(result["city"].upper())].strip()

    result["address_line_2"] = street_part
    return result


def infer_dependents(dependents_text: str) -> Tuple[str, str]:
    value = compact_value(dependents_text)
    if not value or normalize_label(value) == "NONE":
        return "0", "None"

    entries = [item.strip() for item in re.split(r"[;,]", value) if item.strip()]
    ages = []
    for entry in entries:
        age_match = re.search(r"\b(\d{1,2})\b", entry)
        if age_match:
            ages.append(age_match.group(1))
    return str(len(entries)), ", ".join(ages)


def infer_utility_bills(record: Dict[str, Any]) -> str:
    if record.get("utility_bills"):
        return record["utility_bills"]

    raw = record.get("raw_notes", "").lower()
    if "meralco bill" in raw:
        return "Electricity Bill (Meralco)"
    return "None"


def infer_outcome(record: Dict[str, Any]) -> str:
    if record.get("outcome"):
        return record["outcome"]

    remarks = record.get("remarks", "").lower()
    if "confirmed subject residing" in remarks or "confirmed given address" in remarks:
        return "VERIFIED"
    return "PARTIALLY VERIFIED"


def infer_adverse_finding(record: Dict[str, Any]) -> str:
    if record.get("adverse_finding"):
        return record["adverse_finding"]

    remarks = record.get("remarks", "").lower()
    if "unknown ang subject" in remarks or "not known" in remarks:
        return "Not known to neighborhood"
    return "No Adverse Findings"


def infer_living_condition(record: Dict[str, Any]) -> str:
    if record.get("living_condition"):
        return record["living_condition"]

    grade = compact_value(record.get("classification", "") or record.get("house_condition", "")).lower()
    if any(token in grade for token in ["excellent", "very good"]):
        return "Wealthy Living Standard"
    if any(token in grade for token in ["poor", "very bad"]):
        return "Poor Living Standard"
    return "Common Living Standard"


def infer_neighborhood_classification(record: Dict[str, Any]) -> str:
    if record.get("neighborhood_classification"):
        return record["neighborhood_classification"]

    neighborhood = compact_value(record.get("neighborhood", "")).lower()
    if "residential" in neighborhood:
        return "Residential"
    if "commercial" in neighborhood:
        return "Commercial"
    return "Others"


def infer_area_definition(record: Dict[str, Any]) -> str:
    if record.get("area_definition"):
        return record["area_definition"]

    neighborhood = compact_value(record.get("neighborhood", "")).lower()
    accessibility = compact_value(record.get("accessibility", "")).lower()
    if "residential" in neighborhood:
        if "mix" in accessibility:
            return "Mixed Average With Some Parts Poor Residential Area"
        return "Average Residential Area"
    return "Others"


def infer_ownership_verification(record: Dict[str, Any]) -> str:
    if record.get("ownership_verification"):
        return record["ownership_verification"]

    remarks = record.get("remarks", "").lower()
    if "confirmed given address" in remarks:
        return "Verified"
    return "Doubtful"


def infer_basis_of_ownership(record: Dict[str, Any]) -> str:
    if record.get("basis_of_ownership_verification"):
        return record["basis_of_ownership_verification"]

    notes = record.get("raw_notes", "").lower()
    if "brgy" in notes and "official" in notes:
        return "Barangay Officials"
    return "Neighbours"


def parse_named_informant(value: str) -> Dict[str, str]:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if not lines:
        return {"name": "", "relationship": "", "contact": ""}

    primary = lines[0]
    secondary = " ".join(lines[1:]).strip()
    return {
        "name": primary,
        "relationship": secondary,
        "contact": "NP",
    }


def parse_informant_lines(value: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^\d+\.?\s*", "", line)
        segments = [segment.strip() for segment in line.split("/") if segment.strip()]
        name = segments[0] if segments else line
        relationship = segments[1] if len(segments) > 1 else ""
        location = " / ".join(segments[2:]) if len(segments) > 2 else ""
        records.append(
            {
                "name": name,
                "relationship": relationship,
                "address": location,
            }
        )
    return records[:4]


def parse_ci_notes(notes: str) -> Dict[str, Any]:
    record = deepcopy(CI_FORM_DEFAULTS)
    record["raw_notes"] = notes.strip()

    current_person = "subject"
    current_block = ""
    block_buffers: Dict[str, List[str]] = {"remarks": [], "informants": [], "main_informant": [], "dependents": []}

    for raw_line in notes.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        normalized = normalize_label(line)
        if normalized in SECTION_TOKENS:
            current_person = SECTION_TOKENS[normalized]
            current_block = ""
            continue

        if normalized.startswith("REMARKS"):
            current_block = "remarks"
            value = line.split(":", 1)[1].strip() if ":" in line else ""
            if value:
                block_buffers["remarks"].append(value)
            continue

        if normalized == "INFORMANTS":
            current_block = "informants"
            continue

        if normalized.startswith("MAIN INFORMANT"):
            current_block = "main_informant"
            value = line.split(":", 1)[1].strip() if ":" in line else ""
            if value:
                block_buffers["main_informant"].append(value)
            continue

        if normalized.startswith("DEPENDENTS AGE SCHOOL"):
            current_block = "dependents"
            continue

        if ":" not in line and current_block in block_buffers:
            block_buffers[current_block].append(line)
            continue

        if ":" not in line:
            continue

        label, value = [part.strip() for part in line.split(":", 1)]
        normalized_label = normalize_label(label)
        current_block = ""

        if normalized_label in PERSON_FIELD_MAP:
            field_name = f"{current_person}_{PERSON_FIELD_MAP[normalized_label]}"
            record[field_name] = value
            continue

        if current_person == "spouse" and normalized_label in {"EMPLOYMENT", "BUSINESS"}:
            record[f"spouse_{normalized_label.lower()}"] = value
            continue

        if current_person == "subject" and normalized_label in {"EMPLOYMENT", "BUSINESS"}:
            record[f"subject_{normalized_label.lower()}"] = value
            continue

        target_key = DIRECT_FIELD_MAP.get(normalized_label)
        if target_key:
            record[target_key] = value

    record["dependents"] = "\n".join(block_buffers["dependents"]).strip()
    record["remarks"] = "\n".join(block_buffers["remarks"]).strip()
    record["informants"] = "\n".join(block_buffers["informants"]).strip()
    record["main_informant"] = "\n".join(block_buffers["main_informant"]).strip()

    if not record["field_investigator"]:
        record["field_investigator"] = "CI User"
    if not record["submitted_date"]:
        record["submitted_date"] = datetime.now().strftime("%Y-%m-%d")
    if not record["submitted_time"]:
        record["submitted_time"] = datetime.now().strftime("%I:%M %p")
    if not record["date_time_inspected"]:
        record["date_time_inspected"] = f"{record['submitted_date']} {record.get('time_of_visit', '').strip()}".strip()

    return record


def build_export_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(record)
    payload["applicant_name"] = join_name(
        payload.get("subject_last_name", ""),
        payload.get("subject_first_name", ""),
        payload.get("subject_middle_name", ""),
    )
    payload["spouse_name"] = join_name(
        payload.get("spouse_last_name", ""),
        payload.get("spouse_first_name", ""),
        payload.get("spouse_middle_name", ""),
    )
    dependents_count, dependents_ages = infer_dependents(payload.get("dependents", ""))
    payload["dependents_count"] = dependents_count
    payload["dependents_ages"] = dependents_ages
    address_parts = split_address(payload.get("complete_address", ""))
    payload.update(address_parts)
    payload["utility_bills"] = infer_utility_bills(payload)
    payload["living_condition"] = infer_living_condition(payload)
    payload["neighborhood_classification"] = infer_neighborhood_classification(payload)
    payload["area_definition"] = infer_area_definition(payload)
    payload["ownership_verification"] = infer_ownership_verification(payload)
    payload["basis_of_ownership_verification"] = infer_basis_of_ownership(payload)
    payload["adverse_finding"] = infer_adverse_finding(payload)
    payload["outcome"] = infer_outcome(payload)
    payload["main_informant_details"] = parse_named_informant(payload.get("main_informant", ""))
    payload["informant_list"] = parse_informant_lines(payload.get("informants", ""))
    payload["address_type"] = payload.get("address_type") or "Residential Address"
    payload["type_of_residence_export"] = "House and lot" if payload.get("type_of_residence") else ""
    payload["subject_income"] = " / ".join(
        [value for value in [payload.get("subject_employment", ""), payload.get("subject_business", "")] if compact_value(value)]
    )
    payload["spouse_income"] = " / ".join(
        [value for value in [payload.get("spouse_employment", ""), payload.get("spouse_business", "")] if compact_value(value)]
    )
    payload["request_reference"] = (
        payload.get("reference_number")
        or payload.get("los_request_number")
        or payload.get("bpi_request_number")
        or payload.get("account_name")
    )
    payload["date_time_submitted"] = f"{payload.get('submitted_date', '')} {payload.get('submitted_time', '')}".strip()
    payload["residence_description"] = compact_value(
        " | ".join(
            value
            for value in [
                payload.get("type_of_residence", ""),
                payload.get("no_of_storey", ""),
                payload.get("classification", ""),
                payload.get("house_condition", ""),
                payload.get("made_of", ""),
            ]
            if compact_value(value)
        )
    )
    payload["general_appearance"] = compact_value(
        " | ".join(
            value
            for value in [
                payload.get("appearance", ""),
                payload.get("house_color", ""),
                payload.get("gate_color", ""),
                payload.get("fence_color", ""),
                payload.get("exterior", ""),
            ]
            if compact_value(value)
        )
    )
    return payload


def get_available_templates() -> Dict[str, Dict[str, Any]]:
    return TEMPLATE_DEFINITIONS


def get_template_workbook(template_key: str = DEFAULT_TEMPLATE_KEY, template_bytes: bytes | None = None):
    if template_bytes:
        return load_workbook(BytesIO(template_bytes))

    template_path = TEMPLATE_DEFINITIONS[template_key]["path"]
    with open(template_path, "rb") as handle:
        return load_workbook(BytesIO(handle.read()))


def set_value(sheet, cell_ref: str, value: Any) -> None:
    sheet[cell_ref] = "" if value is None else value


def fill_bpi_template(workbook, payload: Dict[str, Any]) -> None:
    sheet = workbook[TEMPLATE_DEFINITIONS["bpi"]["sheet_name"]]
    cell_map = {
        "P4": payload.get("bpi_request_number", ""),
        "P5": payload.get("los_request_number", ""),
        "M8": payload.get("applicant_name", ""),
        "M9": payload.get("subject_civil_status", ""),
        "M10": payload.get("spouse_name", ""),
        "M11": payload.get("dependents_count", ""),
        "AU11": payload.get("dependents_ages", ""),
        "AA13": payload.get("address_type", ""),
        "AA14": payload.get("address_line_1", ""),
        "AA15": payload.get("address_line_2", ""),
        "AA16": payload.get("address_line_3", ""),
        "AA17": payload.get("barangay", ""),
        "AA18": payload.get("city", ""),
        "AA19": payload.get("province", ""),
        "AA20": payload.get("present_address", ""),
        "AA21": payload.get("previous_address", ""),
        "AA22": payload.get("utility_bills", ""),
        "AA23": payload.get("coordinates", ""),
        "U25": payload.get("length_of_stay", ""),
        "U26": payload.get("ownership", ""),
        "U27": payload.get("ownership_verification", ""),
        "U28": payload.get("basis_of_ownership_verification", ""),
        "U29": payload.get("type_of_residence_export", ""),
        "U30": payload.get("living_condition", ""),
        "U32": payload.get("neighborhood_classification", ""),
        "U33": payload.get("area_definition", ""),
        "BA25": payload.get("no_of_storey", ""),
        "BA26": payload.get("parking", ""),
        "AW35": payload.get("adverse_finding", ""),
        "AW36": payload.get("time_of_visit", ""),
        "B39": payload.get("remarks", ""),
        "T43": payload["main_informant_details"].get("name", ""),
        "T44": payload["main_informant_details"].get("relationship", ""),
        "T45": payload["main_informant_details"].get("contact", ""),
        "T52": payload.get("outcome", ""),
        "T56": payload.get("field_investigator", ""),
        "U58": payload.get("submitted_date", ""),
        "AC58": payload.get("submitted_time", ""),
    }

    for cell_ref, value in cell_map.items():
        set_value(sheet, cell_ref, value)

    informant_rows = [47, 48, 49, 50]
    for row_number, informant in zip(informant_rows, payload["informant_list"]):
        set_value(sheet, f"D{row_number}", informant.get("name", ""))
        set_value(sheet, f"V{row_number}", informant.get("relationship", ""))
        set_value(sheet, f"AI{row_number}", informant.get("address", ""))


def fill_maybank_template(workbook, payload: Dict[str, Any]) -> None:
    sheet = workbook[TEMPLATE_DEFINITIONS["maybank"]["sheet_name"]]
    cell_map = {
        "J10": payload.get("request_reference", ""),
        "AB10": payload.get("date_time_inspected", ""),
        "J12": payload.get("requesting_officer", ""),
        "AB12": payload.get("date_time_submitted", ""),
        "F16": payload.get("applicant_name", ""),
        "Q16": payload.get("subject_bday_age", ""),
        "V16": payload.get("subject_education", ""),
        "AG16": payload.get("subject_income", ""),
        "F18": payload.get("subject_civil_status", ""),
        "Q18": payload.get("subject_gender", ""),
        "V18": payload.get("subject_nationality", ""),
        "AG18": payload.get("dependents_count", ""),
        "F20": payload.get("spouse_name", ""),
        "Q20": payload.get("spouse_bday_age", ""),
        "V20": payload.get("spouse_education", ""),
        "AG20": payload.get("spouse_income", ""),
        "F22": payload.get("spouse_civil_status", ""),
        "Q22": payload.get("spouse_gender", ""),
        "V22": payload.get("spouse_nationality", ""),
        "B34": payload.get("address_line_1", ""),
        "I34": payload.get("address_line_2", ""),
        "N34": payload.get("address_line_3", ""),
        "T34": payload.get("barangay", ""),
        "Y34": payload.get("city", ""),
        "AE34": payload.get("province", ""),
        "AJ34": payload.get("region", ""),
        "L37": payload.get("present_address", "") or payload.get("previous_address", ""),
        "J39": payload.get("ownership", ""),
        "AD41": payload.get("ownership", ""),
        "AD42": "",
        "AD43": payload.get("outcome", ""),
        "E49": payload.get("length_of_stay", ""),
        "B53": payload.get("residence_description", ""),
        "W53": payload.get("contact_number", ""),
        "AF53": payload.get("ownership", ""),
        "P54": payload.get("lot_area", ""),
        "P55": payload.get("floor_area", ""),
        "K58": payload.get("vehicles", ""),
        "B61": payload.get("general_appearance", ""),
        "B64": payload.get("utility_bills", ""),
        "K64": payload.get("remarks", ""),
        "W64": payload.get("neighborhood_classification", ""),
        "B71": payload.get("neighborhood", ""),
        "P71": payload.get("accessibility", ""),
        "W71": payload.get("landmark", ""),
        "AF71": payload.get("bdo_distance", ""),
        "B80": payload.get("vehicles", ""),
        "B86": payload.get("remarks", ""),
        "B98": payload["main_informant_details"].get("name", ""),
        "T98": payload["main_informant_details"].get("relationship", ""),
    }

    for cell_ref, value in cell_map.items():
        set_value(sheet, cell_ref, value)

    informant_rows = [98, 99, 100]
    all_informants = payload["informant_list"][:3]
    for row_number, informant in zip(informant_rows, all_informants):
        set_value(sheet, f"B{row_number}", informant.get("name", ""))
        set_value(sheet, f"T{row_number}", informant.get("relationship", ""))


def export_ci_to_template(
    record: Dict[str, Any],
    template_key: str = DEFAULT_TEMPLATE_KEY,
    template_bytes: bytes | None = None,
) -> Tuple[bytes, str]:
    payload = build_export_payload(record)
    workbook = get_template_workbook(template_key=template_key, template_bytes=template_bytes)

    if template_key == "maybank":
        fill_maybank_template(workbook, payload)
    else:
        fill_bpi_template(workbook, payload)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    applicant_slug = re.sub(r"[^A-Za-z0-9]+", "_", payload.get("subject_last_name", "record")).strip("_") or "record"
    filename = f"{template_key}_{applicant_slug}_pdrn_output.xlsx"
    return output.getvalue(), filename


def save_export_copy(file_bytes: bytes, filename: str) -> str:
    export_dir = Path.cwd() / "exports"
    export_dir.mkdir(exist_ok=True)
    output_path = export_dir / filename
    output_path.write_bytes(file_bytes)
    return str(output_path)
