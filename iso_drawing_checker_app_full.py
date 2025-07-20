import streamlit as st
import os
import fitz  # PyMuPDF
import ezdxf
import pandas as pd
import matplotlib.pyplot as plt
from tempfile import NamedTemporaryFile
from fpdf import FPDF

st.set_page_config(page_title="ISO Drawing Checker", layout="wide")

st.title("📐 ISO Drawing Checker")
st.markdown("בדיקת שלמות שרטוטים הנדסיים לפי תקני ISO: העלה קבצי PDF או DXF וקבל דוח מסכם, ציון וטבלת בדיקות.")

uploaded_files = st.file_uploader("העלה קבצים (PDF או DXF)", type=["pdf", "dxf"], accept_multiple_files=True)

# קריטריונים לבדיקה
criteria = {
    "scale": {"label": "קנה מידה", "keywords": ["scale", 'קנ"מ'], "penalty": 20},
    "date": {"label": "תאריך", "keywords": ["date", "תאריך"], "penalty": 15},
    "dimension": {"label": "מידה כללית", "keywords": ["dim", 'מ"מ'], "penalty": 15},
    "signature": {"label": "חתימה", "keywords": ["sign", "חתימה"], "penalty": 10},
}

results = []

def analyze_pdf(file):
    text = ""
    doc = fitz.open(file)
    for page in doc:
        text += page.get_text()
    return text

def analyze_dxf(file):
    doc = ezdxf.readfile(file)
    msp = doc.modelspace()
    dimensions = [e for e in msp if e.dxftype() == 'DIMENSION']
    return len(dimensions)

def check_criteria(text):
    score = 100
    report = []
    for key, info in criteria.items():
        found = any(keyword.lower() in text.lower() for keyword in info["keywords"])
        if not found:
            score -= info["penalty"]
        report.append({
            "קריטריון": info["label"],
            "נמצא?": "✔️" if found else "❌",
            "הערה": "" if found else f"חסר - הורד {info['penalty']}%"
        })
    return score, report

def generate_pdf_report(filename, score, report_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"דוח בדיקה: {filename}", ln=True, align="C")
    pdf.cell(200, 10, txt=f"ציון סופי: {score}%", ln=True, align="C")
    pdf.ln(10)
    for row in report_data:
        pdf.cell(200, 10, txt=f"{row['קריטריון']}: {row['נמצא?']} - {row['הערה']}", ln=True, align="R")
    temp_file = NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

if uploaded_files:
    st.subheader("📊 תוצאות הבדיקה")

    scores = []
    summary_table = []

    for file in uploaded_files:
        ext = os.path.splitext(file.name)[1].lower()
        file_path = NamedTemporaryFile(delete=False, suffix=ext)
        file_path.write(file.read())
        file_path.close()

        try:
            if ext == ".pdf":
                text = analyze_pdf(file_path.name)
                score, report = check_criteria(text)
            elif ext == ".dxf":
                dim_count = analyze_dxf(file_path.name)
                score = 100 if dim_count >= 3 else (85 if dim_count > 0 else 70)
                report = [{
                    "קריטריון": "קווי מידה",
                    "נמצא?": "✔️" if dim_count >= 3 else "❌",
                    "הערה": f"נמצאו {dim_count} קווים"
                }]
            else:
                continue

            scores.append({"שם קובץ": file.name, "ציון": score})
            for row in report:
                row["קובץ"] = file.name
                summary_table.append(row)

            pdf_path = generate_pdf_report(file.name, score, report)
            with open(pdf_path, "rb") as f:
                st.download_button(label=f"הורד דוח PDF עבור {file.name}", data=f.read(),
                                   file_name=f"{file.name}_report.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"שגיאה בקובץ {file.name}: {e}")

    # טבלת סיכום
    df = pd.DataFrame(summary_table)
    df = df[["קובץ", "קריטריון", "נמצא?", "הערה"]]
    st.dataframe(df, use_container_width=True)

    # גרף ציונים
    st.subheader("📈 גרף ציונים לפי קובץ")
    scores_df = pd.DataFrame(scores)
    fig, ax = plt.subplots()
    ax.bar(scores_df["שם קובץ"], scores_df["ציון"], color='skyblue')
    ax.set_ylabel("ציון (%)")
    ax.set_title("ציונים לפי קובץ")
    ax.set_ylim(0, 100)
    st.pyplot(fig)
