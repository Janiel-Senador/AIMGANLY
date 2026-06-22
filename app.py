import json
import os
from io import BytesIO
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

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


def get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        return api_key

    # Streamlit Community Cloud exposes secrets through st.secrets.
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


def main() -> None:
    inject_styles()

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

    with st.sidebar:
        st.subheader("Analysis Settings")
        company_name = st.text_input("Company Name", value="Your Company")
        officer_name = st.text_input("Senior Account Officer", value="")
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


if __name__ == "__main__":
    main()
