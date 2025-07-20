
import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from PIL import Image, ImageDraw
import io

st.set_page_config(page_title="ISO Checker - Visual Tags", layout="wide")
st.title("📏 ISO Drawing Checker with Visual Overlay")
st.markdown("Upload a drawing PDF and expected_tags.csv to see visual summary of tag status.")

uploaded_file = st.file_uploader("Upload PDF drawing", type=["pdf"])
expected_file = st.file_uploader("Upload expected_tags.csv", type=["csv"])

if uploaded_file and expected_file:
    expected_df = pd.read_csv(expected_file)
    expected_tags = expected_df["TAG"].tolist()
    tag_requirements = expected_df.set_index("TAG").to_dict("index")

    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    found_tags = {}
    lines = text.splitlines()
    for line in lines:
        parts = line.strip().split()
        if parts and parts[0] in expected_tags:
            tag = parts[0]
            found_tags[tag] = {
                "X": parts[1] if len(parts) > 1 else "",
                "Y": parts[2] if len(parts) > 2 else "",
                "SIZE": parts[3] if len(parts) > 3 else ""
            }

    results = []
    for tag in expected_tags:
        row = {"TAG": tag}
        found = found_tags.get(tag, {})
        x_ok = bool(found.get("X")) if tag_requirements[tag]["X_required"] else True
        y_ok = bool(found.get("Y")) if tag_requirements[tag]["Y_required"] else True
        s_ok = bool(found.get("SIZE")) if tag_requirements[tag]["SIZE_required"] else True
        row["X"] = found.get("X", "MISSING")
        row["Y"] = found.get("Y", "MISSING")
        row["SIZE"] = found.get("SIZE", "MISSING")
        row["Status"] = "OK" if all([x_ok, y_ok, s_ok]) else "MISSING DATA"
        results.append(row)

    df = pd.DataFrame(results)
    st.dataframe(df)

    # Render image of page 1
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Draw missing items
    offset = 10
    for row in results:
        if row["Status"] != "OK":
            draw.text((10, offset), f"Missing in {row['TAG']}: {', '.join([k for k in ['X', 'Y', 'SIZE'] if row[k]=='MISSING'])}", fill="red")
            offset += 18

    st.image(img, caption="Annotated Drawing with Missing Tags", use_column_width=True)
    st.markdown("✅ Visual overlay complete. Missing fields shown in red.")
