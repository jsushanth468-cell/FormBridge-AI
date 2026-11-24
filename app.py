
# ============================================================
# FORMBRIDGE AI
# PART 1 — FOUNDATION, DESIGN & DOCUMENT INTELLIGENCE
# ============================================================

import streamlit as st
import pandas as pd
import fitz
import re
import io
import json
import hashlib
from datetime import datetime
from difflib import SequenceMatcher
from collections import Counter

# ------------------------------------------------------------
# APPLICATION CONFIGURATION
# ------------------------------------------------------------

st.set_page_config(
    page_title="FormBridge AI | Document Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------

DEFAULT_STATE = {
    "documents": {},
    "analyses": {},
    "chat_history": [],
    "tasks": [],
    "profile": {},
    "eligibility_result": None,
    "last_assistant_answer": "",
    "analysis_history": [],
    "workspace_name": "My Workspace"
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ------------------------------------------------------------
# PREMIUM DESIGN SYSTEM
# ------------------------------------------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 5%, #152b49 0%, transparent 35%),
        radial-gradient(circle at 90% 90%, #172343 0%, transparent 35%),
        #080d18;
    color: #f1f5f9;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

.brand {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
    color: #ffffff;
}

.brand span {
    color: #38bdf8;
}

.hero {
    padding: 35px;
    border-radius: 24px;
    background: linear-gradient(120deg,
        rgba(20,45,78,0.95),
        rgba(26,31,66,0.95));
    border: 1px solid rgba(100,180,255,0.22);
    margin: 20px 0;
}

.hero h1 {
    font-size: 36px;
    font-weight: 800;
    color: #ffffff;
}

.hero p {
    color: #cbd5e1;
    font-size: 16px;
}

.panel {
    background: rgba(17,28,47,0.88);
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 18px;
}

.metric {
    background: linear-gradient(145deg,#14263e,#101a2c);
    border: 1px solid rgba(56,189,248,0.22);
    padding: 20px;
    border-radius: 17px;
    min-height: 115px;
}

.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #38bdf8;
}

.metric-label {
    color: #cbd5e1;
    font-size: 13px;
    margin-top: 5px;
}

.evidence {
    background: rgba(30,55,85,0.55);
    border-left: 4px solid #38bdf8;
    padding: 15px;
    border-radius: 9px;
    margin: 10px 0;
    color: #e2e8f0;
}

h1, h2, h3, h4 {
    color: #f8fafc !important;
}

p, li, label {
    color: #e2e8f0;
}

[data-testid="stMetricValue"] {
    color: #38bdf8;
}

.stButton > button {
    background: linear-gradient(100deg,#0284c7,#2563eb);
    color: white !important;
    border: none;
    border-radius: 11px;
    font-weight: 700;
    padding: 10px 20px;
    transition: 0.2s;
}

.stButton > button:hover {
    background: linear-gradient(100deg,#0ea5e9,#4f46e5);
    border: 1px solid #7dd3fc;
    transform: translateY(-1px);
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background: #101b2d !important;
    color: #ffffff !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
}

[data-testid="stFileUploader"] {
    background: rgba(20,35,58,0.7);
    border: 1px dashed #38bdf8;
    border-radius: 14px;
    padding: 15px;
}

[data-testid="stDataFrame"] {
    border: 1px solid #334155;
    border-radius: 12px;
}

hr {
    border-color: rgba(148,163,184,0.2);
}

.small-muted {
    color: #94a3b8;
    font-size: 12px;
}

.status-good {
    color: #4ade80;
    font-weight: 700;
}

.status-warning {
    color: #fbbf24;
    font-weight: 700;
}

.status-danger {
    color: #fb7185;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# BRAND HEADER
# ------------------------------------------------------------

st.markdown("""
<div class="brand">
    FORM<span>BRIDGE</span> AI
</div>
<div class="small-muted">
    INTELLIGENT DOCUMENT ANALYSIS • DECISION SUPPORT PLATFORM
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>From Confusing Documents<br>to Clear Decisions.</h1>
    <p>
    A unified document intelligence workspace for extracting,
    understanding, comparing and organizing information.
    </p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# TEXT PROCESSING UTILITIES
# ------------------------------------------------------------

def clean_text(text):
    if not text:
        return ""

    text = str(text)
    text = text.replace("\x00", " ")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_words(text):
    return re.findall(r'\b[\w]+\b', text.lower())


def split_sentences(text):
    if not text:
        return []

    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def calculate_hash(text):
    return hashlib.sha256(
        text.encode("utf-8", errors="ignore")
    ).hexdigest()


def extract_pdf(uploaded_file):
    result = []

    pdf = fitz.open(
        stream=uploaded_file.getvalue(),
        filetype="pdf"
    )

    for page_number, page in enumerate(pdf, start=1):
        page_text = page.get_text("text")
        if page_text.strip():
            result.append(
                f"\n[PAGE {page_number}]\n{page_text}"
            )

    pdf.close()
    return clean_text("\n".join(result))


def extract_text_file(uploaded_file):
    raw = uploaded_file.getvalue()

    for encoding in ["utf-8", "utf-16", "latin-1"]:
        try:
            return clean_text(raw.decode(encoding))
        except UnicodeDecodeError:
            continue

    return ""


def extract_document(uploaded_file):
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return extract_pdf(uploaded_file)

    if name.endswith(".txt"):
        return extract_text_file(uploaded_file)

    if name.endswith(".docx"):
        from docx import Document

        document = Document(
            io.BytesIO(uploaded_file.getvalue())
        )

        paragraphs = [
            p.text for p in document.paragraphs if p.text.strip()
        ]

        table_text = []

        for table in document.tables:
            for row in table.rows:
                table_text.append(
                    " | ".join(cell.text for cell in row.cells)
                )

        return clean_text(
            "\n".join(paragraphs + table_text)
        )

    raise ValueError("Unsupported file format")


# ------------------------------------------------------------
# DOCUMENT CLASSIFICATION
# ------------------------------------------------------------

DOCUMENT_CATEGORIES = {
    "Education": [
        "student", "university", "college", "school",
        "admission", "semester", "marks", "degree",
        "certificate", "transcript", "course"
    ],

    "Financial": [
        "income", "salary", "bank", "account",
        "payment", "tax", "revenue", "invoice",
        "balance", "loan", "interest"
    ],

    "Legal": [
        "agreement", "contract", "clause", "legal",
        "party", "obligation", "liability",
        "signature", "terms", "conditions"
    ],

    "Government": [
        "government", "application", "authority",
        "department", "scheme", "certificate",
        "registration", "identity", "official"
    ],

    "Employment": [
        "employee", "employer", "experience",
        "designation", "employment", "resume",
        "candidate", "job", "recruitment"
    ],

    "Medical": [
        "patient", "hospital", "doctor",
        "diagnosis", "medical", "prescription",
        "treatment", "report", "clinical"
    ]
}


def classify_document(text):
    words = get_words(text)

    scores = {}

    for category, keywords in DOCUMENT_CATEGORIES.items():
        scores[category] = sum(
            words.count(keyword) for keyword in keywords
        )

    if not scores or max(scores.values()) == 0:
        return "General Document"

    return max(scores, key=scores.get)


# ------------------------------------------------------------
# INFORMATION EXTRACTION
# ------------------------------------------------------------

DATE_PATTERNS = [
    r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
    r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
    r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
]

REQUIREMENT_KEYWORDS = [
    "must", "required", "mandatory", "should submit",
    "eligible", "minimum", "maximum", "compulsory",
    "necessary", "provide", "attach"
]

WARNING_KEYWORDS = [
    "deadline", "penalty", "late fee", "rejected",
    "invalid", "incomplete", "expired", "not eligible",
    "failure", "strictly"
]

ELIGIBILITY_KEYWORDS = [
    "eligible", "eligibility", "qualification",
    "minimum marks", "minimum age", "maximum age",
    "income limit", "required qualification",
    "criteria", "percentage"
]


def extract_dates(text):
    found = []

    for pattern in DATE_PATTERNS:
        found.extend(re.findall(pattern, text, re.I))

    return list(dict.fromkeys(found))


def extract_requirements(text):
    results = []

    for sentence in split_sentences(text):
        lower = sentence.lower()

        if any(
            keyword in lower
            for keyword in REQUIREMENT_KEYWORDS
        ):
            results.append(sentence)

    return results


def extract_warnings(text):
    results = []

    for sentence in split_sentences(text):
        lower = sentence.lower()

        if any(
            keyword in lower
            for keyword in WARNING_KEYWORDS
        ):
            results.append(sentence)

    return results


def extract_eligibility(text):
    results = []

    for sentence in split_sentences(text):
        lower = sentence.lower()

        if any(
            keyword in lower
            for keyword in ELIGIBILITY_KEYWORDS
        ):
            results.append(sentence)

    return results


# ------------------------------------------------------------
# DOCUMENT ANALYSIS
# ------------------------------------------------------------

def analyse_document(text):
    text = clean_text(text)

    sentences = split_sentences(text)
    words = get_words(text)

    return {
        "category": classify_document(text),
        "word_count": len(words),
        "character_count": len(text),
        "sentence_count": len(sentences),
        "sentences": sentences,
        "dates": extract_dates(text),
        "requirements": extract_requirements(text),
        "warnings": extract_warnings(text),
        "eligibility": extract_eligibility(text),
        "hash": calculate_hash(text),
        "analysed_at": datetime.now().strftime(
            "%d %b %Y, %I:%M %p"
        )
    }

# ============================================================
# END OF PART 1
# PART 2 MUST BE PASTED DIRECTLY BELOW THIS LINE
# ============================================================

# ============================================================
# PART 2 — INTELLIGENCE & DECISION ENGINES
# ============================================================

# ------------------------------------------------------------
# KEYWORD SEARCH ENGINE
# ------------------------------------------------------------

def keyword_search(text, query, context=180):
    if not text or not query:
        return []

    results = []
    pattern = re.compile(re.escape(query), re.I)

    for match in pattern.finditer(text):
        start = max(0, match.start() - context)
        end = min(len(text), match.end() + context)

        results.append({
            "match": match.group(),
            "context": text[start:end].strip(),
            "position": match.start()
        })

        if len(results) >= 30:
            break

    return results


# ------------------------------------------------------------
# DOCUMENT SIMILARITY
# ------------------------------------------------------------

def document_similarity(text_a, text_b):
    words_a = set(get_words(text_a))
    words_b = set(get_words(text_b))

    if not words_a or not words_b:
        return 0.0

    intersection = len(words_a.intersection(words_b))
    union = len(words_a.union(words_b))

    jaccard = intersection / union if union else 0

    sequence = SequenceMatcher(
        None,
        text_a[:5000].lower(),
        text_b[:5000].lower()
    ).ratio()

    return round(
        ((jaccard * 0.65) + (sequence * 0.35)) * 100,
        2
    )


# ------------------------------------------------------------
# NUMERIC CONDITION EXTRACTION
# ------------------------------------------------------------

def extract_numeric_conditions(text):
    patterns = [
        r'(?:minimum|at least|not less than)\s+[\w\s]*?\d+(?:\.\d+)?\s*%?',
        r'(?:maximum|at most|not more than)\s+[\w\s]*?\d+(?:\.\d+)?\s*%?',
        r'\d+(?:\.\d+)?\s*%',
        r'₹\s?[\d,]+(?:\.\d+)?',
        r'\b\d+(?:\.\d+)?\s*(?:years?|months?|days?)\b'
    ]

    results = []

    for pattern in patterns:
        results.extend(
            re.findall(pattern, text, re.I)
        )

    return list(dict.fromkeys(results))


def extract_thresholds(text):
    results = []

    for sentence in split_sentences(text):
        numbers = re.findall(
            r'\d+(?:\.\d+)?',
            sentence
        )

        if numbers:
            results.append({
                "sentence": sentence,
                "numbers": numbers
            })

    return results


# ------------------------------------------------------------
# ELIGIBILITY ENGINE
# ------------------------------------------------------------

def run_eligibility_engine(text, profile):
    conditions = extract_eligibility(text)
    requirements = extract_requirements(text)

    marks = profile.get("marks")
    age = profile.get("age")
    income = profile.get("income")

    checks = []

    for sentence in conditions:
        lower = sentence.lower()

        check = {
            "condition": sentence,
            "status": "Needs review",
            "reason": "Manual verification required"
        }

        numbers = re.findall(
            r'\d+(?:\.\d+)?',
            sentence
        )

        if "minimum marks" in lower or (
            "marks" in lower and "%" in lower
        ):
            if marks is not None and numbers:
                threshold = float(numbers[0])

                if marks >= threshold:
                    check["status"] = "Likely meets"
                    check["reason"] = (
                        f"Your marks ({marks}) meet "
                        f"the stated numeric threshold ({threshold})."
                    )
                else:
                    check["status"] = "Below threshold"
                    check["reason"] = (
                        f"Your marks ({marks}) are below "
                        f"the stated numeric threshold ({threshold})."
                    )

        elif "age" in lower:
            if age is not None and numbers:
                threshold = float(numbers[0])

                if "maximum" in lower or "at most" in lower:
                    passed = age <= threshold
                else:
                    passed = age >= threshold

                check["status"] = (
                    "Likely meets" if passed
                    else "Below threshold"
                )

                check["reason"] = (
                    "Comparison based on the first numeric "
                    "threshold in the sentence."
                )

        elif "income" in lower:
            if income is not None:
                check["reason"] = (
                    "Income condition detected. "
                    "Check the exact currency, period and limit."
                )

        checks.append(check)

    return {
        "checks": checks,
        "conditions_found": len(conditions),
        "requirements_found": len(requirements),
        "profile": profile,
        "disclaimer": (
            "This is an automated preliminary screening tool. "
            "It does not establish official eligibility. "
            "Verify every condition with the issuing authority."
        )
    }


# ------------------------------------------------------------
# CROSS-DOCUMENT ANALYSIS
# ------------------------------------------------------------

def compare_all_documents(documents):
    results = []

    names = list(documents.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name_a = names[i]
            name_b = names[j]

            similarity = document_similarity(
                documents[name_a]["text"],
                documents[name_b]["text"]
            )

            results.append({
                "Document A": name_a,
                "Document B": name_b,
                "Similarity": similarity
            })

    return sorted(
        results,
        key=lambda x: x["Similarity"],
        reverse=True
    )


# ------------------------------------------------------------
# POSSIBLE CONFLICT DETECTOR
# ------------------------------------------------------------

CONFLICT_TOPICS = [
    "date", "deadline", "amount", "income",
    "marks", "percentage", "age", "fee",
    "qualification", "duration", "address",
    "year", "payment"
]


def detect_possible_conflicts(documents):
    findings = []

    names = list(documents.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name_a = names[i]
            name_b = names[j]

            sentences_a = split_sentences(
                documents[name_a]["text"]
            )

            sentences_b = split_sentences(
                documents[name_b]["text"]
            )

            for sentence_a in sentences_a:
                lower_a = sentence_a.lower()

                for sentence_b in sentences_b:
                    lower_b = sentence_b.lower()

                    common_topics = [
                        topic for topic in CONFLICT_TOPICS
                        if topic in lower_a and topic in lower_b
                    ]

                    if not common_topics:
                        continue

                    numbers_a = re.findall(
                        r'\d+(?:\.\d+)?',
                        sentence_a
                    )

                    numbers_b = re.findall(
                        r'\d+(?:\.\d+)?',
                        sentence_b
                    )

                    if numbers_a and numbers_b:
                        if numbers_a != numbers_b:
                            findings.append({
                                "Document A": name_a,
                                "Document B": name_b,
                                "Topic": ", ".join(common_topics),
                                "Evidence A": sentence_a,
                                "Evidence B": sentence_b,
                                "Status": "Possible inconsistency"
                            })

                    if len(findings) >= 100:
                        return findings

    return findings


# ------------------------------------------------------------
# DOCUMENT COMPLETENESS ANALYSIS
# ------------------------------------------------------------

def completeness_analysis(text):
    words = get_words(text)

    checks = {
        "Contains text": len(text.strip()) > 0,
        "Contains dates": len(extract_dates(text)) > 0,
        "Contains requirements": len(extract_requirements(text)) > 0,
        "Contains identifiable category": (
            classify_document(text) != "General Document"
        ),
        "Contains meaningful content": len(words) >= 50
    }

    passed = sum(checks.values())
    total = len(checks)

    return {
        "checks": checks,
        "score": round((passed / total) * 100),
        "passed": passed,
        "total": total
    }


# ------------------------------------------------------------
# EVIDENCE-BASED ASSISTANT
# ------------------------------------------------------------

def build_answer_from_evidence(text, question):
    question_words = set(get_words(question))

    sentences = split_sentences(text)

    ranked = []

    for sentence in sentences:
        sentence_words = set(get_words(sentence))

        overlap = len(
            question_words.intersection(sentence_words)
        )

        if overlap > 0:
            ranked.append({
                "sentence": sentence,
                "score": overlap
            })

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    selected = ranked[:7]

    if not selected:
        return (
            "I couldn't find a strong matching passage "
            "in the available documents. Try using more "
            "specific keywords."
        )

    answer = "Relevant information found in your documents:\n\n"

    for index, item in enumerate(selected, 1):
        answer += (
            f"{index}. {item['sentence']}\n\n"
        )

    answer += (
        "\nPlease verify the original document before "
        "making an important decision."
    )

    return answer


def smart_assistant(question, documents, scope="All Documents"):
    if not documents:
        return "Upload a document before asking questions."

    if scope == "All Documents":
        combined = "\n\n".join(
            item["text"]
            for item in documents.values()
        )
    else:
        combined = documents.get(
            scope, {}
        ).get("text", "")

    if not combined:
        return "No readable text is available in this selection."

    return build_answer_from_evidence(
        combined,
        question
    )


# ------------------------------------------------------------
# ACTION PLAN GENERATOR
# ------------------------------------------------------------

def generate_action_plan(documents):
    actions = []

    for name, document in documents.items():
        analysis = document.get("analysis", {})

        for warning in analysis.get("warnings", []):
            actions.append({
                "Task": f"Review warning in {name}",
                "Details": warning,
                "Priority": "High",
                "Status": "Pending"
            })

        for requirement in analysis.get("requirements", []):
            actions.append({
                "Task": f"Check requirement in {name}",
                "Details": requirement,
                "Priority": "Medium",
                "Status": "Pending"
            })

        for date in analysis.get("dates", []):
            actions.append({
                "Task": f"Verify date in {name}",
                "Details": f"Check date: {date}",
                "Priority": "Medium",
                "Status": "Pending"
            })

    return actions


# ------------------------------------------------------------
# DOCUMENT INSIGHT SUMMARY
# ------------------------------------------------------------

def generate_document_summary(name, document):
    text = document.get("text", "")
    analysis = document.get("analysis", {})

    sentences = analysis.get("sentences", [])

    return {
        "name": name,
        "category": analysis.get("category", "Unknown"),
        "word_count": analysis.get("word_count", 0),
        "opening": sentences[:3],
        "dates": analysis.get("dates", []),
        "requirements": analysis.get("requirements", []),
        "warnings": analysis.get("warnings", []),
        "completeness": completeness_analysis(text)
    }



# ============================================================
# PART 3 — USER INTERFACE & APPLICATION INTEGRATION
# ============================================================

# ------------------------------------------------------------
# NAVIGATION
# ------------------------------------------------------------

PAGES = [
    "Overview",
    "Document Intelligence",
    "Eligibility Engine",
    "Cross-Document Analysis",
    "Smart Assistant",
    "Action Planner",
    "Document Library",
    "Analytics",
    "About"
]

st.markdown("""
<style>
.stRadio > div {
    gap: 8px;
}
.stRadio label {
    background: rgba(30,45,70,0.85);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 9px 13px;
}
.stRadio label,
.stRadio label p,
.stRadio label span,
.stRadio label div {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}
.stRadio label:hover {
    border-color: #38bdf8;
    background: rgba(14,116,144,0.3);
}
.stRadio input:checked + div {
    color: #38bdf8 !important;
}
</style>
""", unsafe_allow_html=True)

selected_page = st.radio(
    "Navigation",
    PAGES,
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")


# ------------------------------------------------------------
# REUSABLE UI FUNCTIONS
# ------------------------------------------------------------

def metric_card(label, value, description=""):
    st.markdown(f"""
    <div class="metric">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        <div class="small-muted">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def page_heading(title, subtitle):
    st.markdown(f"""
    <h1>{title}</h1>
    <p style="color:#94a3b8;">{subtitle}</p>
    """, unsafe_allow_html=True)


def show_evidence(items, empty_message="No information detected."):
    if not items:
        st.info(empty_message)
        return

    for item in items:
        st.markdown(
            f'<div class="evidence">{item}</div>',
            unsafe_allow_html=True
        )


def get_all_text():
    return "\n\n".join(
        item["text"]
        for item in st.session_state.documents.values()
    )


# ------------------------------------------------------------
# DOCUMENT UPLOAD
# ------------------------------------------------------------

def upload_documents(files):
    added = 0
    errors = []

    for uploaded_file in files:
        try:
            text = extract_document(uploaded_file)

            if not text.strip():
                errors.append(
                    f"{uploaded_file.name}: No readable text found."
                )
                continue

            file_hash = calculate_hash(text)

            duplicate = any(
                item["hash"] == file_hash
                for item in st.session_state.documents.values()
            )

            if duplicate:
                continue

            analysis = analyse_document(text)

            st.session_state.documents[uploaded_file.name] = {
                "text": text,
                "hash": file_hash,
                "format": uploaded_file.name.split(".")[-1].upper(),
                "size": len(uploaded_file.getvalue()),
                "added": datetime.now().strftime(
                    "%d %b %Y, %I:%M %p"
                ),
                "analysis": analysis
            }

            st.session_state.analyses[uploaded_file.name] = analysis
            added += 1

        except Exception as error:
            errors.append(
                f"{uploaded_file.name}: {str(error)}"
            )

    return added, errors


def upload_section():
    st.markdown("### Upload your documents")

    files = st.file_uploader(
        "Upload PDF, DOCX or TXT files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="main_document_upload"
    )

    if files:
        if st.button(
            "Process Documents",
            key="process_uploads"
        ):
            added, errors = upload_documents(files)

            if added:
                st.success(
                    f"Successfully processed {added} document(s)."
                )

            for error in errors:
                st.warning(error)

            if not added and not errors:
                st.info(
                    "These documents may already be in your workspace."
                )


# ------------------------------------------------------------
# OVERVIEW
# ------------------------------------------------------------

if selected_page == "Overview":

    page_heading(
        "Command Centre",
        "Your complete document intelligence workspace."
    )

    docs = st.session_state.documents

    total_docs = len(docs)
    total_words = sum(
        d["analysis"]["word_count"] for d in docs.values()
    )
    total_warnings = sum(
        len(d["analysis"]["warnings"]) for d in docs.values()
    )
    total_requirements = sum(
        len(d["analysis"]["requirements"]) for d in docs.values()
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Documents", total_docs, "Files processed")

    with c2:
        metric_card("Words analysed", f"{total_words:,}")

    with c3:
        metric_card("Warnings", total_warnings, "Items requiring review")

    with c4:
        metric_card("Requirements", total_requirements)

    st.markdown("### Workspace")

    upload_section()

    st.markdown("### Recent documents")

    if docs:
        rows = []

        for name, item in docs.items():
            analysis = item["analysis"]

            rows.append({
                "Document": name,
                "Category": analysis["category"],
                "Words": analysis["word_count"],
                "Warnings": len(analysis["warnings"]),
                "Added": item["added"]
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "Your workspace is empty. Upload your first document."
        )

    st.markdown("### Platform capabilities")

    cols = st.columns(3)

    capabilities = [
        ("📄", "Document Intelligence", "Extract information and requirements."),
        ("🎯", "Eligibility Engine", "Compare profile information with document criteria."),
        ("🔗", "Cross-Document Analysis", "Compare multiple documents and flag possible inconsistencies."),
        ("🤖", "Smart Assistant", "Ask questions using document evidence."),
        ("📋", "Action Planner", "Generate tasks from document findings."),
        ("📊", "Analytics", "Explore document insights and statistics.")
    ]

    for index, (icon_text, title, description) in enumerate(capabilities):
        with cols[index % 3]:
            st.markdown(f"""
            <div class="panel">
                <h3>{icon_text} {title}</h3>
                <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)


# ------------------------------------------------------------
# DOCUMENT INTELLIGENCE
# ------------------------------------------------------------

elif selected_page == "Document Intelligence":

    page_heading(
        "Document Intelligence",
        "Extract, understand and investigate document information."
    )

    upload_section()

    docs = st.session_state.documents

    if docs:
        selected_doc = st.selectbox(
            "Select a document",
            list(docs.keys())
        )

        document = docs[selected_doc]
        analysis = document["analysis"]

        st.markdown("### Document overview")

        a, b, c = st.columns(3)

        with a:
            metric_card("Category", analysis["category"])

        with b:
            metric_card("Word count", analysis["word_count"])

        with c:
            metric_card("Sentences", analysis["sentence_count"])

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Summary",
            "Requirements",
            "Dates",
            "Warnings",
            "Full Text"
        ])

        with tab1:
            st.markdown("#### Document classification")
            st.info(analysis["category"])

            st.markdown("#### First extracted passages")
            show_evidence(analysis["sentences"][:5])

        with tab2:
            st.markdown("#### Detected requirements")
            show_evidence(analysis["requirements"])

        with tab3:
            st.markdown("#### Detected dates")
            show_evidence(analysis["dates"])

        with tab4:
            st.markdown("#### Potential warning passages")
            show_evidence(analysis["warnings"])

        with tab5:
            st.text_area(
                "Extracted document text",
                document["text"],
                height=450
            )

        st.markdown("### Search inside document")

        query = st.text_input(
            "Enter a keyword or phrase"
        )

        if query:
            matches = keyword_search(
                document["text"],
                query
            )

            st.write(f"Matches found: {len(matches)}")

            for match in matches:
                show_evidence([match["context"]])

        st.markdown("### Document completeness")

        completeness = completeness_analysis(
            document["text"]
        )

        st.progress(
            completeness["score"] / 100
        )

        st.write(
            f"Completeness indicator: {completeness['score']}%"
        )

        for check, passed in completeness["checks"].items():
            st.write(
                ("✅ " if passed else "⚠️ ") + check
            )


# ------------------------------------------------------------
# ELIGIBILITY ENGINE
# ------------------------------------------------------------

elif selected_page == "Eligibility Engine":

    page_heading(
        "Eligibility Intelligence Engine",
        "Compare your profile with requirements found in uploaded documents."
    )

    docs = st.session_state.documents

    if not docs:
        st.warning("Upload at least one document first.")
    else:
        selected_doc = st.selectbox(
            "Choose the eligibility document",
            list(docs.keys())
        )

        st.markdown("### Profile information")

        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.number_input(
                "Age",
                min_value=0,
                max_value=120,
                value=18
            )

        with col2:
            marks = st.number_input(
                "Marks / Percentage",
                min_value=0.0,
                max_value=100.0,
                value=75.0
            )

        with col3:
            income = st.number_input(
                "Annual income (₹)",
                min_value=0,
                value=0,
                step=10000
            )

        if st.button(
            "Run Eligibility Assessment",
            key="eligibility_run"
        ):

            profile = {
                "age": age,
                "marks": marks,
                "income": income
            }

            result = run_eligibility_engine(
                docs[selected_doc]["text"],
                profile
            )

            st.session_state.eligibility_result = result

        result = st.session_state.eligibility_result

        if result:
            st.markdown("### Assessment results")

            st.info(
                f"Conditions detected: {result['conditions_found']}"
            )

            if result["checks"]:
                for check in result["checks"]:

                    with st.expander(
                        check["condition"],
                        expanded=True
                    ):
                        st.write(
                            f"**Status:** {check['status']}"
                        )

                        st.write(check["reason"])

            else:
                st.warning(
                    "No specific eligibility conditions were detected."
                )

            st.warning(result["disclaimer"])

            st.markdown("### Detected requirements")
            show_evidence(
                docs[selected_doc]["analysis"]["requirements"]
            )


# ------------------------------------------------------------
# CROSS-DOCUMENT ANALYSIS
# ------------------------------------------------------------

elif selected_page == "Cross-Document Analysis":

    page_heading(
        "Cross-Document Intelligence",
        "Compare multiple documents and identify possible differences."
    )

    docs = st.session_state.documents

    if len(docs) < 2:
        st.info(
            "Upload at least two documents to compare them."
        )

    else:
        if st.button(
            "Run Cross-Document Analysis",
            key="cross_analyse"
        ):

            comparisons = compare_all_documents(docs)
            conflicts = detect_possible_conflicts(docs)

            st.session_state["cross_comparisons"] = comparisons
            st.session_state["cross_conflicts"] = conflicts

            st.success("Comparison completed.")

        comparisons = st.session_state.get(
            "cross_comparisons", []
        )

        conflicts = st.session_state.get(
            "cross_conflicts", []
        )

        if comparisons:
            st.markdown("### Similarity comparison")

            st.dataframe(
                pd.DataFrame(comparisons),
                use_container_width=True,
                hide_index=True
            )

        if conflicts:
            st.markdown("### Possible inconsistencies")

            for conflict in conflicts:
                with st.expander(
                    f"{conflict['Topic']} — {conflict['Document A']} / {conflict['Document B']}"
                ):
                    st.write("**Document A evidence**")
                    st.write(conflict["Evidence A"])

                    st.write("**Document B evidence**")
                    st.write(conflict["Evidence B"])

                    st.warning(
                        "Possible difference detected. "
                        "This is a review flag, not proof of a contradiction."
                    )

        elif comparisons:
            st.success(
                "No possible numeric inconsistencies were detected "
                "by the current rules."
            )

        st.caption(
            "Similarity is based on text matching. "
            "Conflict detection is heuristic and requires human verification."
        )


# ------------------------------------------------------------
# SMART ASSISTANT
# ------------------------------------------------------------

elif selected_page == "Smart Assistant":

    page_heading(
        "FormBridge Smart Assistant",
        "Ask questions and retrieve relevant passages from your documents."
    )

    docs = st.session_state.documents

    if not docs:
        st.info("Upload documents to activate document-based search.")
    else:

        scope_options = ["All Documents"] + list(docs.keys())

        scope = st.selectbox(
            "Search scope",
            scope_options
        )

        st.markdown("### Ask your question")

        question = st.text_area(
            "What would you like to understand?",
            placeholder="Example: What are the important deadlines?",
            height=100
        )

        if st.button(
            "Ask FormBridge",
            key="assistant_ask"
        ):

            if question.strip():

                answer = smart_assistant(
                    question,
                    docs,
                    scope
                )

                st.session_state.last_assistant_answer = answer

                st.session_state.chat_history.append({
                    "question": question,
                    "answer": answer,
                    "time": datetime.now().strftime(
                        "%H:%M:%S"
                    )
                })

            else:
                st.warning("Enter a question first.")

        if st.session_state.last_assistant_answer:
            st.markdown("### Answer")

            st.markdown(
                f'<div class="panel">{st.session_state.last_assistant_answer}</div>',
                unsafe_allow_html=True
            )

        st.markdown("### Conversation history")

        for item in reversed(
            st.session_state.chat_history
        ):

            with st.expander(
                item["question"]
            ):
                st.write(item["answer"])
                st.caption(item["time"])


# ------------------------------------------------------------
# ACTION PLANNER
# ------------------------------------------------------------

elif selected_page == "Action Planner":

    page_heading(
        "Intelligent Action Planner",
        "Convert extracted document findings into a review checklist."
    )

    docs = st.session_state.documents

    if not docs:
        st.info("Upload documents to generate action items.")

    else:

        if st.button(
            "Generate Action Plan",
            key="generate_plan"
        ):

            st.session_state.tasks = generate_action_plan(
                docs
            )

            st.success("Action plan generated.")

        tasks = st.session_state.tasks

        if tasks:

            st.markdown("### Generated tasks")

            for index, task in enumerate(tasks):

                with st.container():
                    col1, col2 = st.columns([5, 1])

                    with col1:
                        st.markdown(
                            f"**{index + 1}. {task['Task']}**"
                        )

                        st.write(task["Details"])

                        st.caption(
                            f"Priority: {task['Priority']}"
                        )

                    with col2:
                        if st.button(
                            "Complete",
                            key=f"complete_{index}"
                        ):
                            task["Status"] = "Completed"

                    if task["Status"] == "Completed":
                        st.success("Completed")
                    else:
                        st.warning("Pending")

                    st.divider()

            if st.button(
                "Clear Action Plan",
                key="clear_plan"
            ):
                st.session_state.tasks = []
                st.rerun()

        else:
            st.info(
                "Click Generate Action Plan to create tasks."
            )


# ------------------------------------------------------------
# DOCUMENT LIBRARY
# ------------------------------------------------------------

elif selected_page == "Document Library":

    page_heading(
        "Document Library",
        "Manage all documents in your current workspace."
    )

    docs = st.session_state.documents

    st.write(f"Total documents: {len(docs)}")

    if docs:

        for name, document in docs.items():

            with st.expander(name):

                st.write(
                    f"Format: {document['format']}"
                )

                st.write(
                    f"Size: {document['size']:,} bytes"
                )

                st.write(
                    f"Added: {document['added']}"
                )

                st.write(
                    f"Category: {document['analysis']['category']}"
                )

                if st.button(
                    "Remove Document",
                    key=f"remove_{name}"
                ):
                    del st.session_state.documents[name]
                    st.session_state.analyses.pop(name, None)
                    st.rerun()

        st.markdown("---")

        if st.button(
            "Clear Entire Workspace",
            key="clear_workspace"
        ):

            st.session_state.documents = {}
            st.session_state.analyses = {}
            st.session_state.chat_history = []
            st.session_state.tasks = []
            st.session_state.eligibility_result = None
            st.session_state.last_assistant_answer = ""

            st.rerun()

    else:
        st.info("Your document library is empty.")


# ------------------------------------------------------------
# ANALYTICS
# ------------------------------------------------------------

elif selected_page == "Analytics":

    page_heading(
        "Workspace Analytics",
        "Explore your document processing statistics."
    )

    docs = st.session_state.documents

    if not docs:
        st.info("Upload documents to generate analytics.")

    else:

        category_counts = Counter(
            item["analysis"]["category"]
            for item in docs.values()
        )

        category_df = pd.DataFrame(
            list(category_counts.items()),
            columns=["Category", "Documents"]
        )

        st.markdown("### Document categories")

        st.bar_chart(
            category_df.set_index("Category")
        )

        rows = []

        for name, item in docs.items():

            analysis = item["analysis"]

            rows.append({
                "Document": name,
                "Category": analysis["category"],
                "Words": analysis["word_count"],
                "Sentences": analysis["sentence_count"],
                "Dates": len(analysis["dates"]),
                "Requirements": len(analysis["requirements"]),
                "Warnings": len(analysis["warnings"])
            })

        analytics_df = pd.DataFrame(rows)

        st.markdown("### Document statistics")

        st.dataframe(
            analytics_df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### Export analytics")

        csv_data = analytics_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Analytics CSV",
            data=csv_data,
            file_name="formbridge_analytics.csv",
            mime="text/csv"
        )


# ------------------------------------------------------------
# ABOUT
# ------------------------------------------------------------

elif selected_page == "About":

    page_heading(
        "About FormBridge AI",
        "A document intelligence and decision-support prototype."
    )

    st.markdown("""
    <div class="panel">

    <h2>FORMBRIDGE AI</h2>

    <p>
    FormBridge AI aims to simplify complex documents by
    extracting information, identifying requirements,
    comparing multiple files and organizing actionable findings.
    </p>

    <h3>Core modules</h3>

    <ul>
        <li>Document Intelligence</li>
        <li>Eligibility Assessment</li>
        <li>Cross-Document Comparison</li>
        <li>Evidence-Based Smart Assistant</li>
        <li>Action Planning</li>
        <li>Document Analytics</li>
    </ul>

    <h3>Privacy and processing</h3>

    <p>
    This prototype processes uploaded files within the
    running application. It does not intentionally send
    documents to an external AI service.
    </p>

    <h3>Technology</h3>

    <p>
    Python • Streamlit • PyMuPDF • Pandas • Regular Expressions
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.info(
        "FormBridge AI is a prototype. Its eligibility and "
        "document comparison results are preliminary and "
        "should be verified by a human."
    )


# ------------------------------------------------------------
# EXPORT CENTRE
# ------------------------------------------------------------

st.markdown("---")

st.markdown("### Export Centre")

docs = st.session_state.documents

if docs:

    export_data = {}

    for name, item in docs.items():

        export_data[name] = {
            "format": item["format"],
            "added": item["added"],
            "analysis": item["analysis"]
        }

    json_data = json.dumps(
        export_data,
        indent=4,
        ensure_ascii=False
    )

    st.download_button(
        "Download Workspace Report (JSON)",
        data=json_data,
        file_name="formbridge_workspace_report.json",
        mime="application/json"
    )

else:
    st.caption(
        "Upload documents to enable workspace exports."
    )


# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------

st.markdown("""
<div style="
    text-align:center;
    padding:30px 10px;
    color:#64748b;
    font-size:12px;
">
    <b style="color:#38bdf8;">FORMBRIDGE AI</b><br>
    Document Intelligence • Evidence • Clarity<br>
    Built as an independent document analysis prototype
</div>
""", unsafe_allow_html=True)
