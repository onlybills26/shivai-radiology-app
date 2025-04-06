
# ------------------------------------------------------------------------------
# ShivAI Radiology Reporting App
# © 2024 onlybills26@gmail.com - All Rights Reserved
# This software is proprietary and confidential.
# Unauthorized use, reproduction, distribution, or modification is strictly prohibited.
# Commercial use or resale is not allowed without explicit written permission from the author.
# ------------------------------------------------------------------------------

import streamlit as st
import openai
import requests

# --- Page Setup ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")

# --- OpenAI Setup ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Secure Access ---
if "authenticated" not in st.session_state:
    password = st.text_input("Enter App Password", type="password")
    if password == st.secrets["APP_PASSWORD"]:
        st.session_state.authenticated = True
        st.success("Access granted. Please click below to continue.")
        st.button("Continue")
        st.stop()
    elif password != "":
        st.error("Incorrect password.")
        st.stop()

# --- Embedded Templates ---
EMBEDDED_TEMPLATES = {
    "CT Abdomen": "Type of Study: CT Abdomen\nHistory:\nFindings:\n- Liver: Normal\n- Gallbladder: Normal\nImpression:",
    "CT Chest": "Type of Study: CT Chest\nHistory:\nFindings:\n- Lungs: Clear\nImpression:",
    "MRI Brain": "Type of Study: MRI Brain\nHistory:\nFindings:\n- No infarct or mass\nImpression:",
    "Ultrasound Abdomen": "Type of Study: Ultrasound Abdomen\nHistory:\nFindings:\n- Liver: Normal echotexture\nImpression:",
    "Ultrasound Pelvis": "Type of Study: Ultrasound Pelvis\nHistory:\nFindings:\n- Uterus: Normal\nImpression:"
}

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/onlybills26/radiology-templates/main/"

def detect_template(text):
    keywords = {
        "liver": "CT Abdomen",
        "gallbladder": "CT Abdomen",
        "lung": "CT Chest",
        "nodule": "CT Chest",
        "brain": "MRI Brain",
        "ovary": "Ultrasound Pelvis",
        "uterus": "Ultrasound Pelvis",
        "kidney": "Ultrasound Abdomen"
    }
    for word, template in keywords.items():
        if word in text.lower():
            return template
    return None

def fetch_template(name):
    try:
        url = GITHUB_RAW_BASE + name.replace(" ", "%20") + ".txt"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return EMBEDDED_TEMPLATES.get(name, None)

# --- UI ---
st.title("🚀 ShivAI Radiology Assistant")
mode = st.radio("Choose Mode", ["Report", "Compare"])
auto = st.checkbox("Auto-detect Template", value=True)

if mode == "Compare":
    current = st.text_area("Paste Current Report")
    prior = st.text_area("Paste Prior Report(s)")
    if st.button("Compare & Generate Impression"):
        prompt = f"You are a radiologist. Compare the current report to prior and summarize only significant differences.\n\nCURRENT REPORT:\n{current}\n\nPRIOR REPORTS:\n{prior}"
        with st.spinner("Generating comparative impression..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            st.text_area("Comparative Impression", res.choices[0].message.content, height=300)
else:
    findings = st.text_area("Key Findings / Dictation")
    template_name = detect_template(findings) if auto else st.selectbox("Select Template", list(EMBEDDED_TEMPLATES.keys()))
    st.markdown(f"**Detected Template:** {template_name if template_name else 'None'}")

    if st.button("Generate Report"):
        template = fetch_template(template_name)
        if not template:
            st.error("Template not found. Please select or create it.")
            st.stop()

        prompt = f"You are a radiologist assistant. Use the findings to populate the template. Remove conflicting normals. Format output with: Type of Study, History, Findings, Impression.\n\nTEMPLATE:\n{template}\n\nFINDINGS:\n{findings}"
        with st.spinner("Generating report..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            final = res.choices[0].message.content
            st.text_area("Final Report", final, height=500)
            st.download_button("Copy to Clipboard", final)

# --- Footer ---
st.markdown("---")
st.markdown("© 2024 ShivAI | All Rights Reserved. Unauthorized use or resale prohibited.")
