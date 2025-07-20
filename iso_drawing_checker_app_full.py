import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
from fpdf import FPDF
import os

# הגדרת מחלקה ליצירת דוח PDF
class HebrewPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_page()
        self.add_font('Noto', '', 'NotoSansHebrew-Regular.ttf', uni=True)
        self.set_font('Noto', '', 14)

    def header(self):
        self.set_font('Noto', '', 16)
        self.cell(0, 10, 'דוח בדיקת שרטוט לפי תקן ISO', 0, 1, 'C')

    def add_checklist_table(self, checks):
        self.set_font('Noto', '', 14)
        self.ln(10)
        col_widths = [60, 60]
        self.cell(col_widths[0], 10, "רכיב", border=1, align='C')
        self.cell(col_widths[1], 10, "סטטוס", border=1, align='C')
        self.ln()
        for label, result in checks:
            self.cell(col_widths[0], 10, label, border=1, align='R')
            status = "✓" if result else "✗"
            self.cell(col_widths[1], 10, status, border=1, align='C')
            self.ln()

    def add_score(self, score):
        self.ln(5)
        self.set_font('Noto', '', 12)
        self.cell(0, 10, f"ציון כולל: {score}%", ln=True, align='R')

# פונקציה לבדיקה
def check_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    checks = [
        ("כותרת", "TITLE" in text or "Title" in text),
        ("מספר שרטוט", "DRAWING NUMBER" in text or "Drawing Number" in text),
        ("חתימה", "SIGNATURE" in text or "Signature" in text),
        ("תאריך", "DATE" in text or "Date" in text),
        ("מהדורה", "REVISION" in text or "Revision" in text),
        ("כמות יחידות", "UNITS" in text or "Units" in text),
        ("שם הכותב", "DRAWN BY" in text or "Drawn by" in text),
        ("טבלת מידות", "DIMENSIONS" in text or "Dimensions" in text),
    ]
    return checks

# יצירת דוח
def create_report(file, checks, score):
    report = HebrewPDF()
    report.set_title(file.name)
    report.add_checklist_table(checks)
    report.add_score(score)
    output_filename = file.name.replace(".pdf", "_report.pdf")
    report.output(output_filename)
    return output_filename

# אפליקציה
st.set_page_config(page_title="בודק שרטוטים לפי תקן ISO", layout="wide")
st.title("📏 ISO בודק שרטוטים לפי תקן")
st.markdown("כדי לבדוק אם כל הרכיבים הדרושים קיימים בשרטוט (לפי תקן ISO), העלה קובץ PDF.")

uploaded_files = st.file_uploader("Drag and drop files here", accept_multiple_files=True, type=["pdf"])
if uploaded_files:
    for file in uploaded_files:
        st.subheader(file.name)
        with open(file.name, "wb") as f:
            f.write(file.read())

        checks = check_pdf(file.name)
        df = pd.DataFrame(checks, columns=["רכיב", "value"])
        df["value"] = df["value"].apply(lambda x: "✓" if x else "✗")
        st.table(df)

        score = int(100 * sum(x[1] for x in checks) / len(checks))
        st.write(f"**ציון כולל:** {score}%")

        try:
            report_path = create_report(file, checks, score)
            with open(report_path, "rb") as pdf_file:
                st.download_button("📄 הורד דוח PDF", pdf_file, file_name=report_path)
        except Exception as e:
            st.error(f"שגיאה ביצירת הדוח: {e}")
