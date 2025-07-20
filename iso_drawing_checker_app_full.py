import streamlit as st
import fitz  # PyMuPDF
from fpdf import FPDF
import os

def check_requirements(text):
    results = {
        "כותרת": "title" in text.lower(),
        "מספר שרטוט": "drawing number" in text.lower(),
        "חתימה": "signature" in text.lower(),
        "תאריך": "date" in text.lower(),
        "מהדורה": "revision" in text.lower(),
        "כמות יחידות": "quantity" in text.lower(),
        "שם הכותב": "author" in text.lower(),
        "טבלת מידות": "dimension table" in text.lower()
    }
    return results

def extract_text_from_pdf(pdf_file):
    text = ""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "ISO דוח בדיקה", 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')

    def add_result_table(self, filename, results, score):
        self.add_page()
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, f'קובץ: {filename}', ln=True)
        self.ln(5)
        self.set_font("Arial", '', 12)

        for key, value in results.items():
            result_text = '✓' if value else '✗'
            self.cell(60, 10, f"{key}", border=1)
            self.cell(20, 10, result_text, border=1)
            self.ln()

        self.ln(5)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, f"ציון: {score}%", ln=True)

st.title("🔍 ISO בודק שרטוטים לפי תקן")
st.markdown("כדי לוודא שכל הרכיבים הנדרשים קיימים בשרטוט (לפי ISO), העלה קבצי PDF כאן:")

uploaded_files = st.file_uploader("בחר קבצים", type="pdf", accept_multiple_files=True)

if uploaded_files:
    pdf_report = ReportPDF()

    for file in uploaded_files:
        text = extract_text_from_pdf(file)
        results = check_requirements(text)
        total = len(results)
        passed = sum(results.values())
        score = round((passed / total) * 100)
        pdf_report.add_result_table(file.name, results, score)

        st.subheader(file.name)
        st.table({k: '✓' if v else '✗' for k, v in results.items()})
        st.text(f"ציון כולל: {score}%")

    report_filename = "iso_check_report.pdf"
    pdf_report.output(report_filename)

    with open(report_filename, "rb") as f:
        st.download_button("📥 הורד דוח PDF מסכם", f, file_name=report_filename)
