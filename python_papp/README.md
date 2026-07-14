# Enterprise AI Image Analyzer

A professional Python web application for property, asset, and inspection image analysis using the Gemini API.

This is now the legacy Python version of the project. The active app is the PHP version in `../php_app`.

## Features

- Upload a single image for inspection
- Detect visible objects such as gates, houses, wood, metal, walls, roofs, and more
- Rate each object using:
  - very bad
  - poor
  - fair
  - good
  - very good
  - excellent
- Highlight visible issues like rust, damage, wear, cracks, moisture, and rot
- Show executive summary, risk highlights, and recommendations
- Present a professional dashboard-style interface for enterprise users

## Project Files

- `app.py` - Streamlit user interface
- `gemini_client.py` - Gemini API integration and response parsing
- `requirements.txt` - Python dependencies
- `.env.example` - environment variable template

## Setup

1. Go to the Python app folder and create a virtual environment:

```powershell
cd python_papp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a local `.env` file inside `python_papp`:

```powershell
Copy-Item .env.example .env
```

4. Open `.env` and add your real Gemini API key:

```env
GEMINI_API_KEY=your_real_api_key_here
```

## Run

```powershell
streamlit run app.py
```

## Notes

- The app uses the Gemini image-capable endpoint and sends the uploaded image directly for analysis.
- Results are AI-generated from visible image evidence only.
- For production deployment, keep the API key in environment variables and do not hardcode it in source code.
