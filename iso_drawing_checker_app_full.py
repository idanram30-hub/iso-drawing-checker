import streamlit as st
import pandas as pd
import base64
import fitz  # PyMuPDF
import os
import io
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt

# ---------------------------- CONFIG ----------------------------
REQUIRED_ITEMS = [
    ("כותרת", ["title", "כותרת"], 15),
    ("מספר שרטוט", ["drawing number", "dwg no", "מס' שרטוט"], 15),
    ("גרסה", ["rev", "revision", "גרסה"], 10),
    ("שם חלק", ["part name", "שם החלק"], 10),
    ("קנה מידה", ["scale", "קנ"], 10),
    ("חתימה", ["approved", "חתימה"], 10),
    ("תאריך", ["date", "תאריך"], 10),
    ("יחידות", ["mm", "inch", "unit"], 10),
    ("שם חברה", ["company", "שם חברה"], 5),
    ("טבלת מידות", ["dim", "dimensions"], 5)
]

ISO_7200_FIELDS = ["title", "drawing number", "revision", "date", "approved"]
ISO_129_ELEMENTS = ["dimension line", "extension line", "arrowhead", "tolerance"]
ISO_128_LINES = ["center line", "cutting plane", "hidden line", "section line"]

# ---------------------------- PDF UTILITIES ----------------------------
def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# ---------------------------- ISO CHECKS ----------------------------
def check_iso_7200(text):
    missing = [f for f in ISO_7200_FIELDS if f.lower() not in text.lower()]
    return missing

def check_iso_129(text):
    found = any(term in text.lower() for term in ISO_129_ELEMENTS)
    return found

def check_iso_128(text):
    found = any(term in text.lower() for term in ISO_128_LINES)
    return found

# ---------------------------- CHECK LOGIC ----------------------------
def check_drawing_content(text):
    text = text.lower()
    results = []
    total_score = 0
    max_score = sum(w for _, _, w in REQUIRED_ITEMS)

    for name, keywords, weight in REQUIRED_ITEMS:
        found = any(keyword in text for keyword in keywords)
        score = weight if found else 0
        results.append({"רכיב": name, "נמצא": "✅" if found else "❌", "משקל": weight, "ציון": score})
        total_score += score

    percent = int((total_score / max_score) * 100)
    return results, percent

# ---------------------------- REPORT PDF ----------------------------
class ReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, 'דו"ח בדיקת שרטוט לפי תקן ISO', ln=True, align="C")
        self.ln(10)

    def add_report(self, filename, table, score, iso7200_miss, iso129_ok, iso128_ok):
        self.set_font("Arial", size=12)
        self.cell(0, 10, f"קובץ: {filename} | ציון: {score}%", ln=True)
        self.ln(5)
        self.set_font("Arial", size=10)
        for row in table:
            self.cell(0, 10, f"{row['רכיב']} - {row['נמצא']} (משקל: {row['משקל']})", ln=True)
        self.ln(2)
        self.set_font("Arial", "B", 10)
        self.cell(0, 10, "בדיקות תקן ISO נוספות:", ln=True)
        self.set_font("Arial", size=10)
        self.cell(0, 10, f"ISO 7200 - חסרים שדות: {', '.join(iso7200_miss) if iso7200_miss else '✓'}", ln=True)
        self.cell(0, 10, f"ISO 129 (סימון מידות): {'✓' if iso129_ok else '✗'}", ln=True)
        self.cell(0, 10, f"ISO 128 (קווים מוסכמים): {'✓' if iso128_ok else '✗'}", ln=True)
        self.ln(5)

    def save_pdf(self):
        pdf_io = io.BytesIO()
        self.output(pdf_io)
        pdf_io.seek(0)
        return pdf_io

# ---------------------------- STREAMLIT UI ----------------------------
st.set_page_config(page_title="בודק שרטוטים - ISO", layout="wide")
st.title("📐 בודק שרטוטים לפי תקן ISO")
st.markdown("העלה קבצי שרטוט (PDF בלבד) כדי לבדוק אם כל הרכיבים הדרושים קיימים.")

uploaded_files = st.file_uploader("בחר קבצי PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    report = ReportPDF()
    all_results = []
    all_scores = []

    for file in uploaded_files:
        full_text = extract_text_from_pdf(file)
        results, score = check_drawing_content(full_text)
        df = pd.DataFrame(results)

        iso7200_miss = check_iso_7200(full_text)
        iso129_ok = check_iso_129(full_text)
        iso128_ok = check_iso_128(full_text)

        st.subheader(f"📄 {file.name}")
        st.dataframe(df, use_container_width=True)
        st.markdown("**בדיקות תקן נוספות:**")
        st.write(f"🔹 ISO 7200: חסרים שדות: {', '.join(iso7200_miss) if iso7200_miss else '✓ כל השדות קיימים'}")
        st.write(f"🔹 ISO 129 (מידות): {'✓ נמצא' if iso129_ok else '✗ לא נמצא'}")
        st.write(f"🔹 ISO 128 (קווים): {'✓ נמצא' if iso128_ok else '✗ לא נמצא'}")

        report.add_report(file.name, results, score, iso7200_miss, iso129_ok, iso128_ok)
        all_results.append((file.name, score))
        all_scores.append(score)

    st.markdown("---")
    st.subheader("📊 גרף ציונים")
    fig, ax = plt.subplots()
    labels = [name for name, _ in all_results]
    values = [score for _, score in all_results]
    ax.barh(labels, values, color='skyblue')
    ax.set_xlabel("ציון %")
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("📥 הורדת דוח PDF")
    pdf_bytes = report.save_pdf()
    st.download_button("📄 הורד דוח מסכם", pdf_bytes, file_name="iso_report.pdf")
