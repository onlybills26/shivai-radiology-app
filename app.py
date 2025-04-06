import streamlit as st
import openai
import requests
import io
import time
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

# ------------------------------------------------------------------------------
# ShivAI Radiology Reporting App
# © 2024 onlybills26@gmail.com - All Rights Reserved
# This software is proprietary and confidential.
# Unauthorized use, reproduction, distribution, or modification is strictly prohibited.
# Commercial use or resale is not allowed without explicit written permission from the author.
# ------------------------------------------------------------------------------

# --- Config ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Template Source (Embedded and GitHub fallback) ---
EMBEDDED_TEMPLATES = {
    "CT Abdomen": """Type of Study: CT Abdomen and Pelvis\nHistory:\nFindings:\n- Liver: Normal.\n- Gallbladder: No stones.\n- Pancreas: Normal.\n- Spleen: Normal.\n- Kidneys: No hydronephrosis.\nImpression:""",
    "CT Chest": """Type of Study: CT Chest\nHistory:\nFindings:\n- Lungs: Clear.\n- Mediastinum: Normal.\n- Pleura: No effusion.\nImpression:""",
    "MRI Brain": """Type of Study: MRI Brain\nHistory:\nFindings:\n- No acute infarct.\n- No mass lesion.\nImpression:""",
    "Ultrasound Abdomen": """Type of Study: Ultrasound Abdomen\nHistory:\nFindings:\n- Liver: Normal echotexture.\n- Gallbladder: No stones.\n- CBD: Not dilated.\nImpression:""",
    "Ultrasound Pelvis": """Type of Study: Ultrasound Pelvis (Female)\nHistory:\nFindings:\n- Uterus: Normal size and echotexture.\n- Ovaries: Normal.\nImpression:"""
}

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/onlybills26/radiology-templates/main/"

# --- Auto Template Detection ---
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

# --- Template Fetch ---
def fetch_template(name):
    try:
        url = GITHUB_RAW_BASE + name.replace(" ", "%20") + ".txt"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        st.error(f"Error fetching template from GitHub: {e}")
    return EMBEDDED_TEMPLATES.get(name, None)

# --- Advanced Microphone Integration ---
st.markdown("### 🎙️ Dictation Mode")
st.info("Press the button below to start dictation. The recording will stop automatically after 30 seconds of silence.")

# Use the mic_recorder widget from streamlit-mic-recorder
audio_bytes = mic_recorder("Start Dictation", pause_threshold=1.0)


dictation_text = ""
if audio_bytes is not None:
    st.success("Audio captured. Processing dictation...")
    r = sr.Recognizer()
    try:
        # Assuming the audio_bytes are in WAV format.
        # If not, conversion using pydub or ffmpeg is needed.
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = r.record(source)
        dictation_text = r.recognize_google(audio_data)
        st.text_area("Dictated Text", dictation_text, height=200)
    except sr.UnknownValueError:
        st.error("Speech Recognition could not understand the audio.")
    except sr.RequestError as e:
        st.error(f"Could not request results from the speech recognition service; {e}")
    except Exception as ex:
        st.error(f"An error occurred during audio processing: {ex}")

# --- App Logic ---
st.title("ShivAI Radiology Assistant")
mode = st.radio("Choose Mode", ["Report", "Compare"])
auto = st.checkbox("Auto-detect Template", value=True)

if mode == "Compare":
    current = st.text_area("Paste Current Report")
    prior = st.text_area("Paste Prior Report(s)")
    if st.button("Compare & Generate Impression"):
        prompt = f"You are a radiologist. Compare the current report below to the prior ones and summarize only significant changes.\n\nCURRENT REPORT:\n{current}\n\nPRIOR REPORTS:\n{prior}"
        with st.spinner("Generating comparative impression..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            st.text_area("Comparative Impression", res.choices[0].message.content, height=300)
else:
    # Use either the dictated text or manual text from key findings
    findings_input = st.text_area("Key Findings / Dictation", value=dictation_text)
    template_name = detect_template(findings_input) if auto else st.selectbox("Select Template", list(EMBEDDED_TEMPLATES.keys()))
    st.markdown(f"**Detected Template:** {template_name if template_name else 'None'}")

    if st.button("Generate Report"):
        template = fetch_template(template_name)
        if not template:
            st.error("Template not found. Please check the template name or your internet connection.")
            st.stop()

        prompt = f"You are a radiologist assistant. Use the findings below and insert them into the template provided. Remove any conflicting or redundant lines. Format it with the following headings:\n\nType of Study\nHistory\nFindings\nImpression\n\nTEMPLATE:\n{template}\n\nFINDINGS:\n{findings_input}"
        with st.spinner("Generating report..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            final_report = res.choices[0].message.content
            st.text_area("Final Report", final_report, height=500)
            st.download_button("Copy to Clipboard", final_report)

# --- Footer ---
st.markdown("---")
st.markdown("© 2024 ShivAI | All Rights Reserved. Unauthorized use or resale prohibited.")
