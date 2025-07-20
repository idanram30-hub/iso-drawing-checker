
import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
from fpdf import FPDF
import os

# PDF report generator
class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_font('Arial', '', 12)

    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Drawing ISO Check Report', 0, 1, 'C')

    def add_checklist_table(self, checks):
        self.ln(10)
        col_widths = [70, 30]
        self.cell(col_widths[0], 10, "Item", border=1, align='C')
        self.cell(col_widths[1], 10, "Status", border=1, align='C')
        self.ln()
        for label, result in checks:
            status = "✓" if result else "✗"
            self.cell(col_widths[0], 10, label, border=1)
            self.cell(col_widths[1], 10, status, border=1, align='C')
            self.ln()

    def add_score(self, score):
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"Overall Score: {score}%", ln=True)

# Perform checks on PDF content
def check_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    checks = [
        ("Title", "TITLE" in text or "Title" in text),
        ("Drawing Number", "DRAWING NUMBER" in text or "Drawing Number" in text),
        ("Signature", "SIGNATURE" in text or "Signature" in text),
        ("Date", "DATE" in text or "Date" in text),
        ("Revision", "REVISION" in text or "Revision" in text),
        ("Quantity", "QUANTITY" in text or "Quantity" in text),
        ("Author", "DRAWN BY" in text or "Drawn by" in text),
        ("Dimensions Table", "DIMENSIONS" in text or "Dimensions" in text),
    ]
    return checks

# Create PDF report
def create_report(file, checks, score):
    report = ReportPDF()
    report.set_title(file.name)
    report.add_checklist_table(checks)
    report.add_score(score)
    output_filename = file.name.replace(".pdf", "_report.pdf")
    report.output(output_filename)
    return output_filename

# Streamlit app
st.set_page_config(page_title="ISO Drawing Checker", layout="wide")
st.title("📏 ISO Drawing Checker")
st.markdown("Upload one or more PDF files to check if all required items exist according to ISO standard.")

uploaded_files = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=["pdf"])
if uploaded_files:
    for file in uploaded_files:
        st.subheader(file.name)
        with open(file.name, "wb") as f:
            f.write(file.read())

        checks = check_pdf(file.name)
        df = pd.DataFrame(checks, columns=["Item", "Status"])
        df["Status"] = df["Status"].apply(lambda x: "✓" if x else "✗")
        st.table(df)

        score = int(100 * sum(x[1] for x in checks) / len(checks))
        st.write(f"**Overall Score:** {score}%")

        try:
            report_path = create_report(file, checks, score)
            with open(report_path, "rb") as pdf_file:
                st.download_button("📄 Download PDF Report", pdf_file, file_name=report_path)
        except Exception as e:
            st.error(f"Report generation failed: {e}")
