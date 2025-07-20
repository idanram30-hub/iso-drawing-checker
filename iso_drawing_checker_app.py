import streamlit as st
import os
import fitz  # PyMuPDF
import ezdxf
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="ISO Drawing Checker", layout="centered")

st.title("📐 בדיקת שרטוטים הנדסיים לפי תקני ISO")
st.write("העלה קובץ DXF או PDF, ותקבל ציון כולל על שלמות ותקינות השרטוט לפי תקני ISO.")


uploaded_file = st.file_uploader("בחר קובץ שרטוט (DXF או PDF)", type=["pdf", "dxf"])

if uploaded_file:
    ext = os.path.splitext(uploaded_file.name)[1].lower()

    # Save to temp file
    with NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    score = 100
    issues = []

    if ext == ".pdf":
        st.subheader("📄 ניתוח PDF")
        try:
            doc = fitz.open(tmp_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()

            # Basic ISO checks
            if "scale" not in full_text.lower() and 'קנ"מ' not in full_text:
                issues.append("חסר קנה מידה")
                score -= 20

            if "date" not in full_text.lower() and "תאריך" not in full_text:
                issues.append("חסר תאריך בטבלה")
                score -= 15

            if "dim" not in full_text.lower() and 'מ"מ' not in full_text:
                issues.append("אין מידה כוללת מזוהה")
                score -= 15

            if "sign" not in full_text.lower() and "חתימה" not in full_text:
                issues.append("חסרה חתימת מאשר")
                score -= 10

            st.success("הקובץ נסרק בהצלחה.")

        except Exception as e:
            st.error(f"שגיאה בקריאת הקובץ: {e}")

    elif ext == ".dxf":
        st.subheader("📐 ניתוח DXF")
        try:
            doc = ezdxf.readfile(tmp_path)
            msp = doc.modelspace()
            dimensions = [e for e in msp if e.dxftype() == 'DIMENSION']
            dim_count = len(dimensions)

            if dim_count == 0:
                issues.append("לא נמצאו קווי מידה")
                score -= 30
            elif dim_count < 3:
                issues.append("כמות קווי המידה נמוכה מהמצופה")
                score -= 15

            st.success(f"נמצאו {dim_count} קווי מידה בקובץ.")

        except Exception as e:
            st.error(f"שגיאה בקריאת הקובץ: {e}")

    st.subheader("📊 תוצאה סופית")

    if score < 0:
        score = 0

    st.markdown(f"### ✅ ציון השרטוט: **{score}%**")

    if issues:
        st.markdown("#### ⚠️ בעיות שהתגלו:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("השרטוט עומד בכל הדרישות הידועות לפי תקני ISO שנבדקו.")
