
import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
import io

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

# Perform checks on PDF content and generate annotated images
def check_pdf(path):
    doc = fitz.open(path)
    text = ""
    annotated_images = []

    for i, page in enumerate(doc):
        text += page.get_text()
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Placeholder annotation: mark upper-left with missing items
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

        missing = [label for label, result in checks if not result]
        y_offset = 10
        for label in missing:
            draw.text((10, y_offset), f"Missing: {label}", fill="red")
            y_offset += 15

        annotated_images.append((img, checks))

    return annotated_images

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
st.set_page_config(page_title="ISO Drawing Checker - Annotated", layout="wide")
st.title("📏 ISO Drawing Checker with Annotation")
st.markdown("Upload one or more PDF drawings to get auto-check with visual feedback.")

uploaded_files = st.file_uploader("Upload PDF files", accept_multiple_files=True, type=["pdf"])
if uploaded_files:
    for file in uploaded_files:
        st.subheader(file.name)
        with open(file.name, "wb") as f:
            f.write(file.read())

        annotated_images = check_pdf(file.name)
        for img, checks in annotated_images:
            df = pd.DataFrame(checks, columns=["Item", "Status"])
            df["Status"] = df["Status"].apply(lambda x: "✓" if x else "✗")
            st.table(df)

            score = int(100 * sum(x[1] for x in checks) / len(checks))
            st.write(f"**Overall Score:** {score}%")

            st.image(img, caption="Annotated Drawing", use_column_width=True)

            try:
                report_path = create_report(file, checks, score)
                with open(report_path, "rb") as pdf_file:
                    st.download_button("📄 Download PDF Report", pdf_file, file_name=report_path)
            except Exception as e:
                st.error(f"Report generation failed: {e}")
