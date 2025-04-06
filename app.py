# ------------------------------------------------------------------------------
# ShivAI Radiology Reporting App
# © 2024 onlybills26@gmail.com - All Rights Reserved
# Unauthorized use, resale, or code duplication is strictly prohibited.
# ------------------------------------------------------------------------------

import streamlit as st
import openai
import os
import requests
from streamlit_mic_recorder import mic_recorder, speech_to_text

# --- Password Gate ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter Password", type="password")
    if password == st.secrets["APP_PASSWORD"]:
        st.session_state.authenticated = True
        st.success("Access granted. Please reload the page manually.")
        st.stop()
    else:
        st.warning("Enter correct password to access.")
        st.stop()


# --- Config ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Template Sources ---
EMBEDDED_TEMPLATES = {
    "CT Abdomen": """Type of Study: CT Abdomen and Pelvis\nHistory:\nFindings:\n- Liver: Normal.\n- Gallbladder: No stones.\n- Pancreas: Normal.\n- Spleen: Normal.\n- Kidneys: No hydronephrosis.\nImpression:""",
    "CT Chest": """Type of Study: CT Chest\nHistory:\nFindings:\n- Lungs: Clear.\n- Mediastinum: Normal.\n- Pleura: No effusion.\nImpression:""",
    "MRI Brain": """Type of Study: MRI Brain\nHistory:\nFindings:\n- No acute infarct.\n- No mass lesion.\nImpression:""",
    "Ultrasound Abdomen": """Type of Study: Ultrasound Abdomen\nHistory:\nFindings:\n- Liver: Normal echotexture.\n- Gallbladder: No stones.\n- CBD: Not dilated.\nImpression:""",
    "Ultrasound Pelvis": """Type of Study: Ultrasound Pelvis (Female)\nHistory:\nFindings:\n- Uterus: Normal size and echotexture.\n- Ovaries: Normal.\nImpression:"""
}

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/onlybills26/radiology-templates/main/"

# --- Template Detection Logic ---
def detect_template(text):
    keywords = {
        "liver": "CT Abdomen",
        "gallbladder": "CT Abdomen",
        "lung": "CT Chest",
        "nodule": "CT Chest",
        "brain": "MRI Brain",
        "ovary": "Ultrasound Pelvis",
        "uterus": "Ultrasound Pelvis",
        "CBD": "Ultrasound Abdomen",
        "kidney": "Ultrasound Abdomen"
    }
    for word, template in keywords.items():
        if word in text.lower():
            return template
    return None

# --- Template Fetch Logic ---
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
st.title("ShivAI Radiology Assistant")
mode = st.radio("Choose Mode", ["Report", "Compare"])
auto = st.checkbox("Auto-detect Template", value=True)

# --- Microphone ---
st.markdown("### 🎙️ Dictation Input")
text = mic_recorder(
    start_prompt="🎤 Start Dictation",
    stop_prompt="🛑 Stop Dictation",
    just_once=False,
    use_container_width=True,
)

# --- Mode: Comparison ---
if mode == "Compare":
    current = st.text_area("Paste Current Report")
    prior = st.text_area("Paste Prior Report(s)")
    if st.button("Compare & Generate Impression"):
        prompt = f"You are a radiologist. Compare the current report below to the prior ones and summarize only significant changes. Ignore irrelevant findings like osteophytes or atherosclerosis.\n\nCURRENT REPORT:\n{current}\n\nPRIOR REPORTS:\n{prior}"
        with st.spinner("Generating comparative impression..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            st.text_area("Comparative Impression", res.choices[0].message.content, height=300)

# --- Mode: Reporting ---
else:
    default_text = text if text else ""
    findings = st.text_area("Key Findings / Dictation", value=default_text)
    template_name = detect_template(findings) if auto else st.selectbox("Select Template", list(EMBEDDED_TEMPLATES.keys()))
    st.markdown(f"**Detected Template:** {template_name if template_name else 'None'}")

    if st.button("Generate Report"):
        template = fetch_template(template_name)
        if not template:
            st.error("Template not found. Please check name or connection.")
            st.stop()

        prompt = f"You are a radiologist assistant. You will take the user's findings and inject them into the selected radiology report template. Remove any normal lines that conflict with the findings. Tidy the result. Add a smart impression.\n\nTemplate:\n{template}\n\nFindings:\n{findings}"
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
