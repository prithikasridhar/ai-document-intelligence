# AI-Powered Document Intelligence Platform

A beginner-friendly resume analyzer built with Streamlit, PyMuPDF, Gemini API, Pydantic, and Matplotlib.

## Features
- Upload PDF or TXT resumes, or load the built-in sample resume.
- Extract readable text from PDF/TXT.
- Generate a grounded AI summary in brief, detailed, or bullet-point style.
- Choose Basic, Standard, or Detailed analysis.
- Select fields to focus on.
- Extract name, email, skills, education, work experience, key findings, and uncertain fields.
- Validate structured fields and use null/empty arrays for missing information.
- Display a completeness indicator, skills visual, and downloadable JSON.
- Handle unsupported, unreadable, or nearly empty documents with messages.

## Requirements
- Python 3.10 or newer recommended
- A Gemini API key with access to a free-tier model
- Internet connection for AI analysis

## Setup on Windows
1. Extract the ZIP file.
2. Open the extracted `AI_Document_Intelligence` folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
5. Activate it:
   ```bash
   .venv\Scripts\activate
   ```
6. Install libraries:
   ```bash
   pip install -r requirements.txt
   ```
7. Copy `.env.example` to a new file named `.env`.
8. Open `.env` and replace the placeholder with your key:
   ```text
   GEMINI_API_KEY=your_actual_key
   ```
9. Run the application:
   ```bash
   streamlit run app.py
   ```
10. Browser should open the local Streamlit application. If not, open the local URL shown in the terminal.

## Testing
- Click **Load sample resume**, then click **Analyze document**.
- Upload a text-based PDF resume or a `.txt` resume.
- Try each summary style and analysis level.
- Select individual focus fields.
- Check missing fields, completeness percentage, skills chart, JSON output, and JSON download.
- Test a very short file and a non-PDF/non-TXT file.

## AI service and environment variable
- LLM: Google Gemini API, model configured as `gemini-2.5-flash`.
- Required environment variable: `GEMINI_API_KEY`
- Never commit `.env` or publish the API key.

## Deployment on Render
1. Push the project folder to a GitHub repository. Do not upload `.env`.
2. Sign in to Render and create a new Web Service from the repository.
3. Runtime: Python.
4. Build command: `pip install -r requirements.txt`
5. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
6. In Render's Environment settings, add `GEMINI_API_KEY` with your key.
7. Deploy and test the public URL.

Free-plan availability, sleep behavior, usage limits, and provider policies may change. Do not enable paid billing for this assessment.

## Extraction and validation logic
1. PyMuPDF extracts selectable text from PDF; TXT files are decoded as UTF-8.
2. The extracted source text is sent to Gemini with instructions to use only the source and return JSON.
3. Python parses the JSON and Pydantic validates core field types.
4. Missing name/email values are normalized to null; list fields default to empty arrays.
5. Completeness is calculated using five checks: name, email, skills, education, and work experience. Each available category contributes 20%.

## Analysis levels
- Basic: sends a shorter source excerpt and requests concise extraction.
- Standard: sends a larger excerpt and requests balanced details.
- Detailed: sends the largest excerpt and requests deeper detail.
- Summary style and selected focus fields are passed to the AI prompt.

## Known limitations
- Scanned/image-only PDFs may need OCR; this starter does not include OCR.
- AI extraction can make mistakes; always review results against the original resume.
- The completeness score checks whether key categories are present, not whether the information is factually correct.
- Analysis level changes the prompt and input length; it cannot guarantee different output depth every time.
- Gemini model access and free-tier quotas can change.
- This demo is designed for resumes, not every document category.
- The sample resume is fictional.
