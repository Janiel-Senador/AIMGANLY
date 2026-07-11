import json
import os
from io import BytesIO
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from ci_utils import (
    CI_FORM_DEFAULTS,
    DEFAULT_TEMPLATE_PATH,
    export_ci_to_template,
    parse_ci_notes,
    save_export_copy,
)
from gemini_client import analyze_image_with_gemini


load_dotenv()


st.set_page_config(
    page_title="Enterprise AI Image Analyzer",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)


RATING_ORDER = ["very bad", "poor", "fair", "good", "very good", "excellent"]
RATING_COLORS = {
    "very bad": "#b42318",
    "poor": "#f04438",
    "fair": "#f79009",
    "good": "#12b76a",
    "very good": "#039855",
    "excellent": "#027a48",
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(21, 94, 239, 0.10), transparent 30%),
                    linear-gradient(180deg, #081120 0%, #0b1220 100%);
                color: #e5e7eb;
            }
            .hero {
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(17, 24, 39, 0.85));
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 20px;
                padding: 28px;
                margin-bottom: 18px;
                box-shadow: 0 20px 60px rgba(2, 6, 23, 0.35);
            }
            .hero h1 {
                margin: 0 0 8px 0;
                font-size: 2.2rem;
                color: #f8fafc;
            }
            .hero p {
                margin: 0;
                color: #cbd5e1;
                line-height: 1.6;
            }
            .metric-card {
                background: rgba(15, 23, 42, 0.82);
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 18px;
                padding: 16px 18px;
                min-height: 120px;
            }
            .metric-label {
                color: #94a3b8;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }
            .metric-value {
                color: #f8fafc;
                font-size: 1.8rem;
                font-weight: 700;
                margin-top: 10px;
            }
            .metric-detail {
                color: #cbd5e1;
                margin-top: 8px;
                font-size: 0.95rem;
            }
            .object-card {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 18px;
                padding: 18px;
                margin-bottom: 14px;
            }
            .panel-card {
                background: rgba(15, 23, 42, 0.82);
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 18px;
                padding: 18px;
                margin-bottom: 14px;
            }
            .pill {
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                color: white;
            }
            .section-title {
                color: #f8fafc;
                font-size: 1.05rem;
                font-weight: 700;
                margin: 0 0 8px 0;
            }
            .muted {
                color: #cbd5e1;
            }
            .warning-box {
                background: rgba(127, 29, 29, 0.22);
                border: 1px solid rgba(239, 68, 68, 0.35);
                color: #fecaca;
                border-radius: 14px;
                padding: 14px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def rating_badge(rating: str) -> str:
    normalized = (rating or "fair").strip().lower()
    color = RATING_COLORS.get(normalized, "#475467")
    return f'<span class="pill" style="background:{color};">{normalized}</span>'


def render_metric(label: str, value: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def to_label(value: str) -> str:
    return (value or "Unknown").replace("_", " ").title()


def normalize_objects(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    objects = result.get("objects", [])
    if isinstance(objects, list):
        return [item for item in objects if isinstance(item, dict)]
    return []


def summarize_objects(objects: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {rating: 0 for rating in RATING_ORDER}
    for item in objects:
        rating = str(item.get("rating", "")).strip().lower()
        if rating in counts:
            counts[rating] += 1
    return counts


def render_object_card(item: Dict[str, Any], index: int) -> None:
    object_name = item.get("object_name", f"Object {index}")
    condition = item.get("condition_summary", "No condition summary provided.")
    findings = item.get("findings", [])
    positives = item.get("positive_indicators", [])
    risks = item.get("risk_indicators", [])
    recommendations = item.get("recommendations", [])
    confidence = item.get("confidence", "Medium")
    rating = str(item.get("rating", "fair")).strip().lower()

    st.markdown(
        f"""
        <div class="object-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
                <div>
                    <div class="section-title">{object_name}</div>
                    <div class="muted">Confidence: {to_label(confidence)}</div>
                </div>
                <div>{rating_badge(rating)}</div>
            </div>
            <p class="muted" style="margin-top:12px;">{condition}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.write("Findings")
        st.write(findings if findings else ["No detailed findings provided."])
        st.write("Positive Indicators")
        st.write(positives if positives else ["No positive indicators identified."])
    with col2:
        st.write("Risk Indicators")
        st.write(risks if risks else ["No risk indicators identified."])
        st.write("Recommendations")
        st.write(recommendations if recommendations else ["No recommendations provided."])


def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        return api_key
    return get_secret("GEMINI_API_KEY", "")


def get_users() -> Dict[str, Dict[str, str]]:
    ci_email = get_secret("CI_EMAIL", os.getenv("CI_EMAIL", "janielsenador@gmail.com")).lower()
    ci_password = get_secret("CI_PASSWORD", os.getenv("CI_PASSWORD", "123456"))
    officer_email = get_secret("OFFICER_EMAIL", os.getenv("OFFICER_EMAIL", "officer@company.com")).lower()
    officer_password = get_secret("OFFICER_PASSWORD", os.getenv("OFFICER_PASSWORD", "Officer123!"))

    return {
        ci_email: {
            "password": ci_password,
            "role": "ci",
            "name": "CI User",
        },
        officer_email: {
            "password": officer_password,
            "role": "officer",
            "name": "Senior Account Officer",
        },
    }


def init_session_state() -> None:
    st.session_state.setdefault("auth_user", None)
    st.session_state.setdefault("ci_notes", "")
    st.session_state.setdefault("ci_export_bytes", b"")
    st.session_state.setdefault("ci_export_name", "")
    st.session_state.setdefault("ci_export_path", "")
    for field_name, default_value in CI_FORM_DEFAULTS.items():
        session_key = f"ci_{field_name}"
        st.session_state.setdefault(session_key, default_value)


def seed_ci_form_state(values: Dict[str, Any]) -> None:
    for field_name, value in values.items():
        session_key = f"ci_{field_name}"
        if session_key in st.session_state:
            st.session_state[session_key] = value


def collect_ci_form_data() -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for field_name in CI_FORM_DEFAULTS:
        data[field_name] = st.session_state.get(f"ci_{field_name}", "")
    data["raw_notes"] = st.session_state.get("ci_notes", "")
    return data


def logout() -> None:
    st.session_state["auth_user"] = None
    st.rerun()


def render_login_page() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Enterprise Inspection Portal</h1>
            <p>
                Sign in to continue. Senior Account Officers can access the AI image analyzer,
                while CI users can parse field notes and generate the PDRN workbook.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.1, 0.9])
    with left_col:
        render_metric("Roles", "2", "Officer and CI users have separate dashboards.")
    with right_col:
        render_metric("Security", "Role-Based", "CI users cannot open officer-only image analysis features.")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

    if not submitted:
        return

    users = get_users()
    user_record = users.get(email.strip().lower())
    if not user_record or user_record["password"] != password:
        st.error("Invalid email or password.")
        return

    st.session_state["auth_user"] = {
        "email": email.strip().lower(),
        "role": user_record["role"],
        "name": user_record["name"],
    }
    st.rerun()


def render_officer_dashboard(user: Dict[str, str]) -> None:
    with st.sidebar:
        st.subheader("Session")
        st.write(f"Signed in as `{user['name']}`")
        st.write("Role: `Officer`")
        st.divider()
        company_name = st.text_input("Company Name", value="Your Company")
        officer_name = st.text_input("Senior Account Officer", value=user["name"])
        inspection_context = st.text_area(
            "Inspection Context",
            value=(
                "Assess visible objects, structures, and materials. Highlight quality issues such as "
                "rust, damage, rot, moisture, wear, poor maintenance, or strong overall condition."
            ),
            height=160,
        )
        strict_mode = st.checkbox(
            "Use stricter quality ratings",
            value=True,
            help="When enabled, the AI becomes more conservative and flags visible risks more aggressively.",
        )
        st.caption("The rating scale is: very bad, poor, fair, good, very good, excellent.")
        if st.button("Sign Out", use_container_width=True):
            logout()

    st.markdown(
        """
        <div class="hero">
            <h1>Enterprise AI Image Analyzer</h1>
            <p>
                Upload a site, property, asset, or inspection image and receive an AI-generated
                assessment of visible objects, their condition, potential risks, and a quality rating
                from very bad to excellent.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload image",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
        help="Upload a clear image of a house, gate, building material, vehicle, property, or any inspection scene.",
    )

    if not uploaded_file:
        st.info("Upload an image to begin the AI analysis.")
        return

    image_bytes = uploaded_file.getvalue()
    image = Image.open(BytesIO(image_bytes))

    preview_col, action_col = st.columns([1.2, 1.8])
    with preview_col:
        st.image(image, caption=uploaded_file.name, use_container_width=True)
    with action_col:
        st.subheader("Inspection Request")
        st.write(f"Company: `{company_name}`")
        st.write(f"Officer: `{officer_name or 'Not specified'}`")
        st.write(f"Context: {inspection_context}")
        analyze_clicked = st.button("Analyze Image", type="primary", use_container_width=True)

    if not analyze_clicked:
        return

    api_key = get_gemini_api_key()
    if not api_key:
        st.error(
            "Missing `GEMINI_API_KEY`. Add it to your local `.env` file or to Streamlit Cloud app secrets."
        )
        st.stop()

    with st.spinner("Analyzing image and evaluating object quality..."):
        result = analyze_image_with_gemini(
            api_key=api_key,
            image_bytes=image_bytes,
            image_mime_type=uploaded_file.type or "image/jpeg",
            company_name=company_name,
            officer_name=officer_name,
            inspection_context=inspection_context,
            strict_mode=strict_mode,
        )

    if result.get("error"):
        st.markdown(
            f'<div class="warning-box">{result["error"]}</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    objects = normalize_objects(result)
    counts = summarize_objects(objects)
    overall_rating = str(result.get("overall_rating", "fair")).strip().lower()
    overall_summary = result.get("overall_summary", "No summary returned.")
    priority_risks = result.get("priority_risks", [])
    recommendations = result.get("overall_recommendations", [])
    detected_scene = result.get("scene_type", "General inspection")

    st.subheader("Executive Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric("Overall Rating", to_label(overall_rating), overall_summary)
    with col2:
        render_metric("Scene Type", detected_scene, "AI-estimated inspection context based on visible elements.")
    with col3:
        render_metric("Objects Found", str(len(objects)), "Count of analyzed visible objects or structures.")
    with col4:
        critical_count = counts["very bad"] + counts["poor"]
        render_metric("Critical Issues", str(critical_count), "Objects flagged as very bad or poor.")

    st.subheader("Rating Distribution")
    dist_cols = st.columns(len(RATING_ORDER))
    for idx, rating in enumerate(RATING_ORDER):
        with dist_cols[idx]:
            render_metric(to_label(rating), str(counts[rating]), "Detected object count")

    if priority_risks:
        st.subheader("Priority Risks")
        for risk in priority_risks:
            st.warning(risk)

    if recommendations:
        st.subheader("Management Recommendations")
        for recommendation in recommendations:
            st.success(recommendation)

    st.subheader("Object-by-Object Analysis")
    if not objects:
        st.info("The AI did not return specific objects for this image.")
    else:
        for idx, item in enumerate(objects, start=1):
            render_object_card(item, idx)

    with st.expander("Raw JSON Result"):
        st.code(json.dumps(result, indent=2), language="json")

    st.caption(
        "AI results are based only on visible image evidence. Final business or structural decisions should be validated by a qualified human inspector."
    )


def render_ci_dashboard(user: Dict[str, str]) -> None:
    with st.sidebar:
        st.subheader("Session")
        st.write(f"Signed in as `{user['name']}`")
        st.write("Role: `CI`")
        st.divider()
        if DEFAULT_TEMPLATE_PATH.exists():
            st.success(f"Template found: `{DEFAULT_TEMPLATE_PATH.name}`")
        else:
            st.warning("Default template path is not available. Upload the template file below.")
        if st.button("Sign Out", use_container_width=True):
            logout()

    st.markdown(
        """
        <div class="hero">
            <h1>CI Notes to PDRN Workbook</h1>
            <p>
                Paste CI notes, auto-fill the case data, review the parsed fields, and generate
                a filled PDRN workbook using the existing template format. CI users cannot access
                the officer image-analysis module.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    notes_col, template_col = st.columns([1.3, 0.9])
    with notes_col:
        st.subheader("CI Notes")
        st.text_area(
            "Paste the CI notes here",
            key="ci_notes",
            height=380,
            placeholder="Paste the full CI notes and click 'Autofill From Notes'.",
        )
        button_col1, button_col2 = st.columns(2)
        with button_col1:
            if st.button("Autofill From Notes", type="primary", use_container_width=True):
                parsed = parse_ci_notes(st.session_state.get("ci_notes", ""))
                if not st.session_state.get("ci_field_investigator"):
                    parsed["field_investigator"] = user["name"]
                seed_ci_form_state(parsed)
                st.success("CI notes parsed. Review the fields below before generating the workbook.")
        with button_col2:
            if st.button("Clear Parsed Fields", use_container_width=True):
                seed_ci_form_state(CI_FORM_DEFAULTS)
                st.session_state["ci_notes"] = ""
                st.session_state["ci_export_bytes"] = b""
                st.session_state["ci_export_name"] = ""
                st.session_state["ci_export_path"] = ""
                st.rerun()

    with template_col:
        st.subheader("Workbook Template")
        render_metric(
            "Template Source",
            "Default" if DEFAULT_TEMPLATE_PATH.exists() else "Upload Required",
            str(DEFAULT_TEMPLATE_PATH),
        )
        template_upload = st.file_uploader(
            "Optional Template Upload",
            type=["xls", "xlsx"],
            key="ci_template_upload",
            help="Upload the PDRN template if the default path is not available.",
        )

    st.subheader("Parsed CI Fields")
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    with info_col1:
        render_metric(
            "Applicant",
            st.session_state.get("ci_subject_last_name", "") or "Pending",
            "Primary subject details parsed from the notes.",
        )
    with info_col2:
        render_metric(
            "Residence",
            st.session_state.get("ci_type_of_residence", "") or "Pending",
            "Residence and property observation summary.",
        )
    with info_col3:
        informants_count = len(
            [line for line in st.session_state.get("ci_informants", "").splitlines() if line.strip()]
        )
        render_metric("Informants", str(informants_count), "Number of parsed third-party informants.")
    with info_col4:
        render_metric(
            "Outcome",
            st.session_state.get("ci_outcome", "") or "Pending",
            "Verification result to be written into the workbook.",
        )

    subject_col1, subject_col2, subject_col3 = st.columns(3)
    with subject_col1:
        st.text_input("Account Name", key="ci_account_name")
        st.text_input("Subject Last Name", key="ci_subject_last_name")
        st.text_input("Subject First Name", key="ci_subject_first_name")
        st.text_input("Subject Middle Name", key="ci_subject_middle_name")
        st.text_input("Nickname", key="ci_subject_nickname")
    with subject_col2:
        st.text_input("Birthday / Age", key="ci_subject_bday_age")
        st.text_input("Birthplace", key="ci_subject_birthplace")
        st.text_input("Civil Status", key="ci_subject_civil_status")
        st.text_input("Nationality", key="ci_subject_nationality")
        st.text_input("Educational Attainment", key="ci_subject_education")
    with subject_col3:
        st.text_input("Employment Source", key="ci_subject_employment")
        st.text_input("Business Source", key="ci_subject_business")
        st.text_input("Spouse Name", key="ci_spouse_first_name")
        st.text_input("Spouse Civil Status", key="ci_spouse_civil_status")
        st.text_area("Dependents / Ages / School", key="ci_dependents", height=126)

    address_col1, address_col2 = st.columns(2)
    with address_col1:
        st.text_area("Complete Address", key="ci_complete_address", height=100)
        st.text_input("Present Address", key="ci_present_address")
        st.text_input("Previous Address", key="ci_previous_address")
        st.text_input("Province", key="ci_province")
        st.text_input("Length of Stay", key="ci_length_of_stay")
        st.text_input("Contact Number", key="ci_contact_number")
    with address_col2:
        st.text_input("Ownership", key="ci_ownership")
        st.text_input("Type of Residence", key="ci_type_of_residence")
        st.text_input("No. of Storey", key="ci_no_of_storey")
        st.text_input("Classification", key="ci_classification")
        st.text_input("House Condition", key="ci_house_condition")
        st.text_input("Made Of", key="ci_made_of")

    property_col1, property_col2, property_col3 = st.columns(3)
    with property_col1:
        st.text_input("Appearance", key="ci_appearance")
        st.text_input("Accessibility", key="ci_accessibility")
        st.text_input("Neighborhood", key="ci_neighborhood")
        st.text_input("Vehicles", key="ci_vehicles")
    with property_col2:
        st.text_input("House Color", key="ci_house_color")
        st.text_input("Gate Color", key="ci_gate_color")
        st.text_input("Fence Color", key="ci_fence_color")
        st.text_input("Parking", key="ci_parking")
    with property_col3:
        st.text_input("Lot Area", key="ci_lot_area")
        st.text_input("Floor Area", key="ci_floor_area")
        st.text_input("Landmark", key="ci_landmark")
        st.text_input("Corner", key="ci_corner")

    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.text_input("Time of Visit", key="ci_time_of_visit")
        st.text_input("Utility Bills / IDs", key="ci_utility_bills")
        st.text_input("Coordinates", key="ci_coordinates")
        st.text_input("Ownership Verification", key="ci_ownership_verification")
        st.text_input("Basis of Ownership Verification", key="ci_basis_of_ownership_verification")
    with export_col2:
        st.text_input("Living Condition", key="ci_living_condition")
        st.text_input("Neighborhood Classification", key="ci_neighborhood_classification")
        st.text_input("Area Definition", key="ci_area_definition")
        st.text_input("Adverse Finding", key="ci_adverse_finding")
        st.text_input("Outcome", key="ci_outcome")

    st.text_area("Remarks", key="ci_remarks", height=180)
    st.text_area("Informants", key="ci_informants", height=140)
    st.text_area("Main Informant", key="ci_main_informant", height=100)

    footer_col1, footer_col2, footer_col3 = st.columns(3)
    with footer_col1:
        st.text_input("Field Investigator", key="ci_field_investigator")
    with footer_col2:
        st.text_input("Submitted Date", key="ci_submitted_date")
    with footer_col3:
        st.text_input("Submitted Time", key="ci_submitted_time")

    generate_clicked = st.button("Generate PDRN Workbook", type="primary", use_container_width=True)
    if generate_clicked:
        record = collect_ci_form_data()
        template_bytes = template_upload.getvalue() if template_upload else None
        if not template_bytes and not DEFAULT_TEMPLATE_PATH.exists():
            st.error("Template file not found. Upload the PDRN template to continue.")
        else:
            try:
                file_bytes, filename = export_ci_to_template(record, template_bytes=template_bytes)
                saved_path = save_export_copy(file_bytes, filename)
                st.session_state["ci_export_bytes"] = file_bytes
                st.session_state["ci_export_name"] = filename
                st.session_state["ci_export_path"] = saved_path
                st.success("Workbook generated successfully.")
            except Exception as exc:
                st.error(f"Unable to generate the workbook: {exc}")

    if st.session_state.get("ci_export_bytes"):
        st.download_button(
            "Download Generated Workbook",
            data=st.session_state["ci_export_bytes"],
            file_name=st.session_state["ci_export_name"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.caption(f"Local copy saved to: `{st.session_state['ci_export_path']}`")

    with st.expander("Parsed CI Data (JSON)"):
        st.code(json.dumps(collect_ci_form_data(), indent=2), language="json")


def main() -> None:
    inject_styles()
    init_session_state()

    user = st.session_state.get("auth_user")
    if not user:
        render_login_page()
        return

    if user["role"] == "ci":
        render_ci_dashboard(user)
        return

    render_officer_dashboard(user)


if __name__ == "__main__":
    main()
