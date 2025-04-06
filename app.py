import streamlit as st
import openai
import requests
import io
import time
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

# --------------------------------------------------------------------
# ShivAI Radiology Reporting App
# © 2024 onlybills26@gmail.com - All Rights Reserved
# --------------------------------------------------------------------

# --- Config ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Embedded Templates ---
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

from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import queue
import threading

st.markdown("### 🎙️ Dictation Mode")
st.info("Speak into your mic. Dictation starts immediately after allowing access.")

audio_queue = queue.Queue()

# Audio processor
def audio_frame_callback(frame: av.AudioFrame) -> av.AudioFrame:
    audio_queue.put(frame.to_ndarray().flatten().tobytes())
    return frame

# Start WebRTC streamer
webrtc_ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDONLY,
    in_audio=True,
    audio_frame_callback=audio_frame_callback,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

dictation_text = ""

def recognize_from_queue():
    r = sr.Recognizer()
    audio_bytes = b''.join(list(audio_queue.queue))
    if len(audio_bytes) == 0:
        return None
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio_data = r.record(source)
    return r.recognize_google(audio_data)

if webrtc_ctx.state.playing:
    st.warning("Listening... Speak now.")
    if st.button("Stop & Transcribe"):
        with st.spinner("Transcribing audio..."):
            try:
                dictation_text = recognize_from_queue()
                if dictation_text:
                    st.success("Dictation captured:")
                    st.text_area("Dictated Text", dictation_text, height=200)
                else:
                    st.error("No speech detected.")
            except sr.UnknownValueError:
                st.error("Could not understand audio.")
            except Exception as e:
                st.error(f"Error during recognition: {e}")


# --- Main UI ---
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
