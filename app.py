import streamlit as st
import openai
import os

# --- PASSWORD PROTECTION ---
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
# --- Streamlit Setup ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Template System ---
TEMPLATE_DIR = "templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

def list_templates():
    return [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".txt")]

# --- Sidebar: Template Management ---
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
    selected = st.sidebar.selectbox("Select Template", list_templates())
    if selected:
        with open(f"{TEMPLATE_DIR}/{selected}", "r") as f:
            current = f.read()
        edited = st.sidebar.text_area("Edit", value=current)
        if st.sidebar.button("Update"):
            with open(f"{TEMPLATE_DIR}/{selected}", "w") as f:
                f.write(edited)
            st.sidebar.success("Updated.")

elif template_action == "Delete":
    selected = st.sidebar.selectbox("Delete Which?", list_templates())
    if selected and st.sidebar.button("Delete"):
        os.remove(f"{TEMPLATE_DIR}/{selected}")
        st.sidebar.warning(f"{selected} deleted.")
# --- Main UI ---
st.title("ShivAI Radiology Report Generator")

mode = st.radio("Choose Mode", ["Dictate/Type Findings", "Paste Full Report", "Compare Reports"])

# --- Compare Mode ---
if mode == "Compare Reports":
    st.subheader("🟢 Current Report")
    current = st.text_area("Paste Current Report")
    st.subheader("🟡 Prior Reports")
    prior = st.text_area("Paste Previous Report(s)")
    
    if st.button("Compare"):
        compare_prompt = f"""
You are a senior radiologist assistant. Compare the CURRENT report to the PRIOR reports and highlight only clinically meaningful changes. 
Ignore differences in formatting, wording, or non-significant items like osteophytes, vascular calcifications, or artifacts.

CURRENT REPORT:
{current}

PRIOR REPORTS:
{prior}
"""
        with st.spinner("Generating comparison..."):
            res = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": compare_prompt}]
            )
            st.text_area("Comparative Impression", res.choices[0].message.content, height=300)
# --- Dictate / Paste Report Mode ---
else:
    selected_template = st.selectbox("Select Template", list_templates())
    input_text = st.text_area("📝 Dictate or Paste Findings")

    if st.button("Generate Report"):
        if not selected_template:
            st.warning("Please select a template first.")
            st.stop()

        with open(f"{TEMPLATE_DIR}/{selected_template}", "r") as f:
            template = f.read()

        base_prompt = f"""
You are a highly skilled radiologist assistant.

1. Start with this base report template below.
2. Remove any lines that contradict the FINDINGS provided.
3. Inject the abnormal findings clearly and concisely.
4. Clean the language and format it neatly.
5. Automatically add an appropriate IMPRESSION at the end.
6. The technique section should match the modality (e.g., CT, MRI).
7. Make sure all sections flow naturally and nothing contradictory remains.

TEMPLATE:
{template}

FINDINGS:
{input_text}
"""

        with st.spinner("Generating final report..."):
            res = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": base_prompt}]
            )
            st.text_area("📄 Final Report", res.choices[0].message.content, height=500)




