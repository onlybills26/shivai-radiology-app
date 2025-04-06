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

# --- TEMPLATE MANAGEMENT ---
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

# --- DICTATION COMPONENT ---
def mic_input(label):
    st.markdown(f"**{label}**")
    components.html("""
    <script>
    const startDictation = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = true;
        recognition.interimResults = false;

        let lastInputTime = Date.now();
        let timeoutId;

        recognition.onresult = function(event) {
            let transcript = event.results[event.resultIndex][0].transcript;
            let textarea = window.parent.document.querySelector('textarea');
            if (textarea) {
                textarea.value += transcript + " ";
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
            lastInputTime = Date.now();
        }

        recognition.onend = function() {
            let now = Date.now();
            if (now - lastInputTime < 30000) {
                recognition.start();
            }
        }

        recognition.start();
    }
    </script>
    <button onclick="startDictation()">🎤 Start Dictation</button>
    """, height=40)

# --- TEMPLATE SUGGESTION ---
def guess_template(text):
    keywords = {
        "lung": "CT Chest.txt",
        "liver": "CT Abdomen.txt",
        "ovary": "Ultrasound Pelvis.txt",
        "brain": "MRI Brain.txt",
        "thyroid": "Ultrasound Thyroid.txt",
    }
    for key, template in keywords.items():
        if key in text.lower():
            return template
    return None

# --- MAIN INTERFACE ---
st.title("ShivAI Radiology Report Generator")
mode = st.radio("Choose Mode", ["Dictate / Type Findings", "Compare Reports"])

if mode == "Dictate / Type Findings":
    mic_input("🎤 Dictate Findings (Optional)")
    input_text = st.text_area("Enter key findings or paste here")
    default_template = guess_template(input_text)

    selected_template = st.selectbox("Select Template (optional)", ["Auto Detect"] + list_templates())
    use_template = default_template if selected_template == "Auto Detect" else selected_template

    if st.button("Generate Report"):
        if not use_template or not os.path.exists(f"{TEMPLATE_DIR}/{use_template}"):
            st.warning("No suitable template found.")
            st.stop()

        with open(f"{TEMPLATE_DIR}/{use_template}", "r") as f:
            template = f.read()

        prompt = f"You are a radiologist assistant. You will take the user's findings and inject them into the selected radiology report template. Remove any normal lines that conflict with the findings. Tidy the result. Add a smart impression.\n\nTemplate:\n{template}\n\nFindings:\n{input_text}"

        with st.spinner("Generating report..."):
            res = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            final_report = res.choices[0].message.content
            st.text_area("Final Report", final_report, height=500, key="final_output")
            st.button("📋 Copy to Clipboard", on_click=st.experimental_set_query_params, args=("copied",))

elif mode == "Compare Reports":
    mic_input("🎤 Dictate Current Report (Optional)")
    current = st.text_area("🟢 Current Report")
    prior = st.text_area("🟡 Prior Reports")

    if st.button("Compare & Generate Impression"):
        compare_prompt = f"You are a radiologist. Compare the current report below to the prior ones and summarize only significant changes. Ignore irrelevant findings like osteophytes or atherosclerosis.\n\nCURRENT REPORT:\n{current}\n\nPRIOR REPORTS:\n{prior}"
        with st.spinner("Generating comparative impression..."):
            res = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": compare_prompt}]
            )
            st.text_area("🧠 Comparative Impression", res.choices[0].message.content, height=300)