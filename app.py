import streamlit as st
import openai
import os
import requests
from difflib import unified_diff
from streamlit_mic_recorder import mic_recorder

# --- Streamlit Config ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")

# --- Constants ---
TEMPLATE_DIR = "templates"
FALLBACK_TEMPLATE_URL = "https://raw.githubusercontent.com/onlybills26/shivai-templates/main"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# --- API Key ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Footer License ---
st.markdown("""
---
<center>
© 2024 ShivAI by onlybills26. All rights reserved. Protected by MIT/Proprietary license.
</center>
""", unsafe_allow_html=True)

# --- Helper: Load Template ---
def load_template(name):
    local_path = os.path.join(TEMPLATE_DIR, f"{name}.txt")
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            return f.read()
    # Try GitHub fallback
    url = f"{FALLBACK_TEMPLATE_URL}/{name.replace(' ', '%20')}.txt"
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, "w") as f:
            f.write(response.text)
        return response.text
    return None

# --- Template Manager ---
def list_templates():
    return [f[:-4] for f in os.listdir(TEMPLATE_DIR) if f.endswith(".txt")]

def save_template(name, content):
    with open(os.path.join(TEMPLATE_DIR, f"{name}.txt"), "w") as f:
        f.write(content)

# --- Sidebar ---
st.sidebar.title("Template Tools")
action = st.sidebar.radio("Action", ["Use", "Add", "Edit", "Delete"])

if action == "Add":
    name = st.sidebar.text_input("Template Name")
    content = st.sidebar.text_area("Template Content")
    if st.sidebar.button("Save"):
        save_template(name, content)
        st.sidebar.success("Saved")

elif action == "Edit":
    sel = st.sidebar.selectbox("Select Template", list_templates())
    with open(os.path.join(TEMPLATE_DIR, f"{sel}.txt"), "r") as f:
        content = f.read()
    edited = st.sidebar.text_area("Edit Content", value=content)
    if st.sidebar.button("Update"):
        save_template(sel, edited)
        st.sidebar.success("Updated")

elif action == "Delete":
    sel = st.sidebar.selectbox("Select Template", list_templates())
    if st.sidebar.button("Delete"):
        os.remove(os.path.join(TEMPLATE_DIR, f"{sel}.txt"))
        st.sidebar.warning(f"Deleted {sel}")

# --- Mic Dictation ---
dictation_text = ""
with st.expander("🎙️ Start Dictation"):
    audio = mic_recorder(start_prompt="Click to Dictate", stop_prompt="Stop Recording", key="mic")
    if audio and "text" in audio:
        dictation_text = audio["text"]

# --- Report Generation ---
st.title("ShivAI Radiology Assistant")
mode = st.radio("Mode", ["Dictate / Type Findings", "Paste Full Report", "Compare Reports"])

if mode == "Compare Reports":
    curr = st.text_area("Current Report")
    prior = st.text_area("Prior Report(s)")
    show_diff = st.checkbox("Show Changes")
    if st.button("Generate Comparison"):
        prompt = f"You are a radiologist. Compare current and prior reports. Show only significant changes. Ignore osteophytes and vascular calcifications.\n\nCURRENT:\n{curr}\n\nPRIOR:\n{prior}"
        with st.spinner("Generating..."):
            res = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            output = res.choices[0].message.content
            st.text_area("Comparative Impression", output, height=300)
            if show_diff:
                diffs = unified_diff(prior.splitlines(), curr.splitlines(), lineterm="")
                st.code("\n".join(diffs))

else:
    input_text = st.text_area("Key Findings / Dictation", value=dictation_text)
    auto_detect = st.checkbox("Auto-detect template", value=True)
    selected = st.selectbox("Or Select Template", list_templates()) if not auto_detect else None

    if st.button("Generate Report"):
        template_name = None

        if auto_detect:
            # basic detection logic
            for t in list_templates():
                if t.lower().replace("ct ", "") in input_text.lower():
                    template_name = t
                    break
        else:
            template_name = selected

        template = load_template(template_name) if template_name else None

        if not template:
            st.error(f"Template '{template_name}' not found. Please create it or select manually.")
            st.stop()

        # GPT Prompt
        base_prompt = f"""
        You are a radiologist assistant. Take the user's findings and inject them into the selected radiology template.
        Remove normal/conflicting lines. Format the output as:

        Type of Study: [Infer or use from template name]
        History: [leave blank if not dictated]

        Findings:
        [Structured findings with smart formatting]

        Impression:
        [Summarize abnormalities only. No repetition.]

        Template:
        {template}

        Findings:
        {input_text}
        """

        with st.spinner("Generating report..."):
            res = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": base_prompt}]
            )
            final = res.choices[0].message.content
            st.text_area("Final Report", final, height=500)
            st.download_button("📋 Copy to Clipboard", final, file_name="report.txt")

# --- Requirements Reminder ---
# streamlit
# openai
# streamlit_mic_recorder
# requests
