import json
import os
from typing import List, Optional

import matplotlib.pyplot as plt
import streamlit as st
import fitz  # PyMuPDF
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, EmailStr, Field, ValidationError

load_dotenv()

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")


class ResumeData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    work_experience: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    uncertain_fields: List[str] = Field(default_factory=list)


def extract_text(uploaded_file):
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        try:
            doc = fitz.open(
                stream=uploaded_file.getvalue(),
                filetype="pdf"
            )
            text = "\n".join(page.get_text("text") for page in doc)
            doc.close()
            return text.strip()
        except Exception as exc:
            raise ValueError(
                "Unable to read the PDF file. The file may be corrupted."
            ) from exc

    if name.endswith(".txt"):
        try:
            return uploaded_file.getvalue().decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError(
                "The text file is not in UTF-8 format. Please upload a UTF-8 text file."
            ) from exc

    raise ValueError("Please upload a PDF or TXT file only.")


def get_ai_result(document_text, summary_style, analysis_level, focus_fields):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Please check the .env file."
        )

    client = genai.Client(api_key=api_key)

    max_chars = {
        "Basic": 8000,
        "Standard": 16000,
        "Detailed": 24000
    }[analysis_level]

    source = document_text[:max_chars]

    style_instructions = {
        "Brief": "Write a short summary of about 3-5 sentences.",
        "Detailed": "Write a detailed summary with key points and relevant evidence.",
        "Bullet points": "Write the summary as clear bullet points."
    }

    prompt = f"""
You are a careful resume document analyst. Use ONLY the source text below.
Do not invent facts. If a field is missing, use null for name/email and [] for list fields.
If information is unclear, mention it in uncertain_fields. Return valid JSON only with exactly
these keys: summary, name, email, skills, education, work_experience, key_findings, uncertain_fields.
summary must be a string. name and email must be strings or null. The remaining fields must be arrays of strings.
Do not infer an email address or qualification that is not stated in the source.
Focus fields requested by user: {", ".join(focus_fields) if focus_fields else "all fields"}.
Analysis level: {analysis_level}.
Summary style: {summary_style}. {style_instructions[summary_style]}
At Basic level, keep extraction concise. At Standard level, include all clearly stated relevant details.
At Detailed level, include more context and list relevant entries separately.
SOURCE DOCUMENT:
{source}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )

    raw = response.text or ""

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The AI did not return valid JSON. Please try again."
        ) from exc

    result.setdefault("summary", "")

    for key in ["name", "email"]:
        result.setdefault(key, None)

        if result[key] in ("", "Not provided", "N/A", "null"):
            result[key] = None

    for key in [
        "skills",
        "education",
        "work_experience",
        "key_findings",
        "uncertain_fields"
    ]:
        result.setdefault(key, [])

        if not isinstance(result[key], list):
            result[key] = []

    validated = ResumeData(
        name=result["name"],
        email=result["email"],
        skills=result["skills"],
        education=result["education"],
        work_experience=result["work_experience"],
        key_findings=result["key_findings"],
        uncertain_fields=result["uncertain_fields"],
    )

    result.update(validated.model_dump())

    return result


def completeness_score(data):
    checks = [
        bool(data.get("name")),
        bool(data.get("email")),
        bool(data.get("skills")),
        bool(data.get("education")),
        bool(data.get("work_experience")),
    ]

    return round(sum(checks) / len(checks) * 100)


st.title("📄 AI-Powered Document Intelligence")

st.caption(
    "Upload a resume, get an AI summary, structured fields, and a visual skills overview."
)

with st.sidebar:
    st.header("Analysis settings")

    summary_style = st.selectbox(
        "Summary style",
        ["Brief", "Detailed", "Bullet points"]
    )

    analysis_level = st.selectbox(
        "Analysis level",
        ["Basic", "Standard", "Detailed"],
        index=1
    )

    focus_fields = st.multiselect(
        "Focus on specific fields",
        [
            "Name and email",
            "Skills",
            "Education",
            "Work experience",
            "Key findings"
        ],
        default=[
            "Name and email",
            "Skills",
            "Education",
            "Work experience",
            "Key findings"
        ]
    )

    st.info(
        "Basic = concise • Standard = balanced • Detailed = deeper extraction"
    )


sample_path = os.path.join(
    os.path.dirname(__file__),
    "sample_documents",
    "sample_resume.txt"
)

if os.path.exists(sample_path):
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_text = f.read()
else:
    sample_text = ""


left, right = st.columns([3, 2])

with left:
    uploaded_file = st.file_uploader(
        "Upload resume (PDF or TXT)",
        type=["pdf", "txt"]
    )

with right:
    if st.button("Load sample resume"):
        st.session_state["sample_mode"] = True

    st.caption("You can use the sample resume button for testing.")


if uploaded_file is not None:
    try:
        document_text = extract_text(uploaded_file)
    except ValueError as error:
        st.error(str(error))
        st.stop()

elif st.session_state.get("sample_mode"):
    document_text = sample_text

else:
    document_text = ""


if document_text and len(document_text.strip()) < 30:
    st.warning(
        "The document contains very little readable text. Please try another file."
    )
    st.stop()


if document_text:
    with st.expander("View extracted source text"):
        st.text(document_text[:12000])

        if len(document_text) > 12000:
            st.caption(
                "The preview displays only the first 12,000 characters."
            )

    if st.button("Analyze document", type="primary"):
        with st.spinner("AI is analyzing your resume..."):
            try:
                result = get_ai_result(
                    document_text,
                    summary_style,
                    analysis_level,
                    focus_fields
                )

                st.session_state["analysis_result"] = result
                st.session_state["analysis_text_length"] = len(document_text)

            except Exception as error:
                st.error(f"Analysis failed: {error}")
                st.caption(
                    "Please check the API key, internet connection, model access, and free-tier quota."
                )


result = st.session_state.get("analysis_result")

if result:
    st.divider()

    st.subheader("AI Summary")
    st.write(result.get("summary") or "Summary is not available.")

    data = result
    score = completeness_score(data)

    c1, c2, c3 = st.columns(3)

    c1.metric("Completeness", f"{score}%")
    c2.metric("Skills found", len(data.get("skills", [])))
    c3.metric("Education entries", len(data.get("education", [])))

    st.progress(score / 100)

    st.subheader("Extracted information")

    display_fields = [
        ("Name", "name", "Name and email"),
        ("Email", "email", "Name and email"),
        ("Skills", "skills", "Skills"),
        ("Education", "education", "Education"),
        ("Work experience", "work_experience", "Work experience"),
        ("Key findings", "key_findings", "Key findings"),
    ]

    for label, key, focus in display_fields:
        if focus in focus_fields:
            value = data.get(key)

            st.markdown(f"**{label}**")

            if value is None or value == [] or value == "":
                st.warning(
                    f"{label}: Information not found (null/empty)."
                )

            elif isinstance(value, list):
                for item in value:
                    st.write(f"- {item}")

            else:
                st.write(value)

    if data.get("uncertain_fields"):
        st.subheader("Fields to review")

        for item in data["uncertain_fields"]:
            st.warning(item)

    skills = data.get("skills", [])

    if skills:
        st.subheader("Visual insight: Skills overview")

        counts = [1] * len(skills)

        fig, ax = plt.subplots(
            figsize=(8, max(2.5, len(skills) * 0.45))
        )

        ax.barh(skills[::-1], counts[::-1])
        ax.set_xlabel("Mentioned in resume")
        ax.set_title("Skills identified")
        ax.set_xlim(0, 1.2)

        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

    st.subheader("Structured JSON")

    json_output = {
        "summary": result.get("summary"),
        "name": result.get("name"),
        "email": result.get("email"),
        "skills": result.get("skills"),
        "education": result.get("education"),
        "work_experience": result.get("work_experience"),
        "key_findings": result.get("key_findings"),
        "uncertain_fields": result.get("uncertain_fields"),
        "completeness_percentage": score,
    }

    st.json(json_output)

    st.download_button(
        "Download extracted JSON",
        data=json.dumps(
            json_output,
            indent=2,
            ensure_ascii=False
        ),
        file_name="resume_analysis.json",
        mime="application/json"
    )


st.divider()

st.caption(
    "Privacy note: Uploaded document text is sent to the configured Gemini API for analysis. Use test resumes and avoid uploading sensitive documents without permission."
)
