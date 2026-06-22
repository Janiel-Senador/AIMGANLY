import base64
import json
import re
from typing import Any, Dict

import requests


GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-flash-latest:generateContent"
)


def build_prompt(company_name: str, officer_name: str, inspection_context: str, strict_mode: bool) -> str:
    strictness = (
        "Be strict and conservative. Visible damage, rust, moisture, cracks, rot, poor finishing, "
        "corrosion, or weak maintenance should lower ratings."
        if strict_mode
        else "Be balanced and objective. Use only visible evidence in the image."
    )
    return f"""
You are an enterprise-grade image inspection AI for {company_name}.
Inspector name: {officer_name or "Not provided"}.
Inspection context: {inspection_context}

Analyze the uploaded image carefully.
Detect all major visible objects, structures, and materials that are relevant for condition assessment.
Examples include gate, fence, house, roof, wall, window, door, vehicle, concrete, wood, metal, flooring, stairs, soil, and surrounding exterior elements.

For every relevant object:
- Identify the object name
- Describe its visible condition
- Criticize the quality honestly
- Mention defects such as rust, dents, cracks, discoloration, wetness, dry rot, decay, corrosion, sagging, peeling paint, mold, broken parts, or wear if visible
- Mention positive signs if visible
- Give exactly one rating from this fixed scale:
  very bad, poor, fair, good, very good, excellent
- Provide a confidence of low, medium, or high
- Provide practical recommendations

Rules:
- Only use evidence visible in the image
- Do not invent hidden structural issues
- If an object is visible but condition cannot be judged well, say that clearly and lower confidence
- Use concise professional business language
- {strictness}

Return only valid JSON using this exact structure:
{{
  "scene_type": "string",
  "overall_rating": "very bad|poor|fair|good|very good|excellent",
  "overall_summary": "string",
  "priority_risks": ["string"],
  "overall_recommendations": ["string"],
  "objects": [
    {{
      "object_name": "string",
      "rating": "very bad|poor|fair|good|very good|excellent",
      "confidence": "low|medium|high",
      "condition_summary": "string",
      "findings": ["string"],
      "positive_indicators": ["string"],
      "risk_indicators": ["string"],
      "recommendations": ["string"]
    }}
  ]
}}
""".strip()


def parse_json_response(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced_match = re.search(r"```json\s*(\{[\s\S]*\})\s*```", text, re.IGNORECASE)
    if fenced_match:
        try:
            return json.loads(fenced_match.group(1))
        except json.JSONDecodeError:
            pass

    object_match = re.search(r"(\{[\s\S]*\})", text)
    if object_match:
        try:
            return json.loads(object_match.group(1))
        except json.JSONDecodeError:
            pass

    return {"error": "The AI returned an unreadable response. Please try again with a clearer image."}


def analyze_image_with_gemini(
    api_key: str,
    image_bytes: bytes,
    image_mime_type: str,
    company_name: str,
    officer_name: str,
    inspection_context: str,
    strict_mode: bool,
) -> Dict[str, Any]:
    prompt = build_prompt(company_name, officer_name, inspection_context, strict_mode)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": image_mime_type,
                            "data": base64.b64encode(image_bytes).decode("utf-8"),
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    try:
        response = requests.post(
            f"{GEMINI_ENDPOINT}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=90,
        )
    except requests.RequestException as exc:
        return {"error": f"Unable to reach Gemini API: {exc}"}

    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {"error": {"message": response.text}}
        message = error_payload.get("error", {}).get("message", "Unknown Gemini API error.")
        return {"error": f"Gemini API error: {message}"}

    try:
        data = response.json()
    except ValueError:
        return {"error": "Gemini API returned a non-JSON response."}

    candidates = data.get("candidates", [])
    if not candidates:
        return {"error": "Gemini API returned no candidates."}

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if not text:
        return {"error": "Gemini API returned an empty response."}

    result = parse_json_response(text)
    if "objects" not in result:
        result["objects"] = []
    if "priority_risks" not in result:
        result["priority_risks"] = []
    if "overall_recommendations" not in result:
        result["overall_recommendations"] = []
    return result
