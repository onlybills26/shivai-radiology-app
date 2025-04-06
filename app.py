import streamlit as st
import os
import openai
from openai import OpenAI
import streamlit.components.v1 as components

# --- PASSWORD GATE ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "shivaccess2024":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        st.error("Incorrect password")
        st.stop()

check_password()

# --- SETUP ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# --- Template Management ---
TEMPLATE_DIR = "templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

def list_templates():
    return [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".txt")]

st.sidebar.title("Templates")
template_action = st.sidebar.radio("Manage Templates", ["Use Template", "Add", "Edit", "Delete"])

if template_action == "Add":
    name = st.sidebar.text_input("New Template Name")
    content = st.sidebar.text_area("Template Content")
    if st.sidebar.button("Save"):
        with open(f"{TEMPLATE_DIR}/{name}.txt", "w") as f:
            f.write(content)
        st.sidebar.success("Template saved.")

elif template_action == "Edit":
    selected = st.sidebar.selectbox("Select Template to Edit", list_templates())
    if selected:
        with open(f"{TEMPLATE_DIR}/{selected}", "r") as f:
            current = f.read()
        edited = st.sidebar.text_area("Edit Template", value=current)
        if st.sidebar.button("Update"):
            with open(f"{TEMPLATE_DIR}/{selected}", "w") as f:
                f.write(edited)
            st.sidebar.success("Template updated.")

elif template_action == "Delete":
    selected = st.sidebar.selectbox("Select Template to Delete", list_templates())
    if selected and st.sidebar.button("Delete"):
        os.remove(f"{TEMPLATE_DIR}/{selected}")
        st.sidebar.warning(f"{selected} deleted.")
def mic_input(label):
    st.markdown(f"**{label}**")
    components.html("""
    <script>
    let streamlitInput = window.parent.document.querySelector('textarea');
    let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    function startDictation() {
        recognition.start();
    }

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        streamlitInput.value += transcript;
        streamlitInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
    </script>
    <button onclick="startDictation()">🎤 Start Dictation</button>
    """, height=40)
# --- MAIN UI ---
st.title("ShivAI Radiology Report Generator")
mode = st.radio("Choose Mode", ["Dictate / Type Findings", "Compare Reports"])

# --- REPORT GENERATION MODE ---
if mode == "Dictate / Type Findings":
    selected_template = st.selectbox("Select Template", list_templates())
    mic_input("🎤 Dictate Findings (Optional)")
    findings = st.text_area("📝 Key Findings or Dictation")

    if st.button("Generate Report"):
        if not selected_template:
            st.warning("Please select a template.")
            st.stop()
        with open(f"{TEMPLATE_DIR}/{selected_template}", "r") as f:
            template = f.read()

        prompt = f"""
You are a radiologist assistant. Use the template below. Replace conflicting normals, inject abnormal findings, and add a structured IMPRESSION at the end.

TEMPLATE:
{template}

FINDINGS:
{findings}
"""

        with st.spinner("Generating report..."):
            res = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            st.text_area("📄 Final Report", res.choices[0].message.content, height=500)

# --- COMPARISON MODE ---
elif mode == "Compare Reports":
    mic_input("🎤 Dictate Current Report (Optional)")
    current = st.text_area("🟢 Current Report")
    prior = st.text_area("🟡 Prior Reports (one or more)")

    if st.button("Compare & Generate Impression"):
        compare_prompt = f"""
You are a radiologist. Compare the CURRENT report to PRIOR reports and summarize only significant clinical changes. 
Ignore formatting, phrasing differences, osteophytes, atherosclerosis, or incidental calcifications.

CURRENT REPORT:
{current}

PRIOR REPORTS:
{prior}
"""

        with st.spinner("Generating comparative impression..."):
            res = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": compare_prompt}]
            )
            st.text_area("🧠 Comparative Impression", res.choices[0].message.content, height=300)




