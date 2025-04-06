import streamlit as st
import openai
import os
import difflib
from datetime import datetime

# --- ShivAI Radiology Reporting App ---
# © 2024 onlybills26. All Rights Reserved.
# Unauthorized copying, distribution, or modification is prohibited.

# --- Streamlit Config ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")

# --- Secure API Key Handling ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Template Storage Directory ---
TEMPLATE_DIR = "templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# --- Helper Functions ---
def list_templates():
    return [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".txt")]

def load_template(name):
    with open(f"{TEMPLATE_DIR}/{name}", "r") as f:
        return f.read()

def save_template(name, content):
    with open(f"{TEMPLATE_DIR}/{name}", "w") as f:
        f.write(content)

def delete_template(name):
    os.remove(f"{TEMPLATE_DIR}/{name}")

# --- Sidebar: Template Management ---
st.sidebar.title("Templates")
template_action = st.sidebar.radio("Manage Templates", ["Use Template", "Add Template", "Edit Template", "Delete Template"])

if template_action == "Add Template":
    new_name = st.sidebar.text_input("Template Name")
    new_content = st.sidebar.text_area("Template Content")
    if st.sidebar.button("Save Template"):
        save_template(f"{new_name}.txt", new_content)
        st.sidebar.success("Template saved.")

elif template_action == "Edit Template":
    selected = st.sidebar.selectbox("Select Template", list_templates())
    if selected:
        current = load_template(selected)
        edited = st.sidebar.text_area("Edit Template", value=current)
        if st.sidebar.button("Update Template"):
            save_template(selected, edited)
            st.sidebar.success("Template updated.")

elif template_action == "Delete Template":
    selected = st.sidebar.selectbox("Select Template", list_templates())
    if selected and st.sidebar.button("Delete Template"):
        delete_template(selected)
        st.sidebar.warning(f"Deleted {selected}")

# --- Access Control ---
password = st.text_input("Enter Access Password", type="password")
if password != st.secrets.get("app_password", "shivaccess2024"):
    st.stop()

# --- Main Title ---
st.title("ShivAI Radiology Report Generator")

mode = st.radio("Select Mode", ["Dictate/Type Findings", "Paste Full Report", "Compare Reports"])

# --- Compare Mode ---
if mode == "Compare Reports":
    st.subheader("Current Report")
    current = st.text_area("Paste Current Report")
    st.subheader("Prior Reports")
    prior = st.text_area("Paste Previous Report(s)")
    show_diff = st.checkbox("Show Changes")
    if st.button("Compare & Generate Impression"):
        prompt = f"You are a radiologist. Compare the current report below to the prior ones and summarize only significant changes. Ignore irrelevant findings like osteophytes or atherosclerosis.\n\nCURRENT REPORT:\n{current}\n\nPRIOR REPORTS:\n{prior}"
        with st.spinner("Generating comparative impression..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            comparison = res.choices[0].message.content
            st.text_area("Comparative Impression", comparison, height=300)
            if show_diff:
                diff = difflib.unified_diff(prior.splitlines(), current.splitlines(), lineterm="")
                st.code("\n".join(diff), language="diff")

# --- Dictation / Report Generation ---
else:
    findings = st.text_area("Key Findings / Dictation")
    detect_template = st.checkbox("Auto-detect Template", value=True)
    selected_template = None

    if not detect_template:
        selected_template = st.selectbox("Or Select Template", list_templates())

    if st.button("Generate Report"):
        if detect_template:
            detection_prompt = f"Select the most appropriate radiology template name (e.g. 'CT Chest', 'MRI Brain', 'Ultrasound Pelvis') for the following findings:\n\n{findings}\n\nOnly reply with the template name."
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": detection_prompt}]
            )
            selected_template = response.choices[0].message.content.strip()

        if not selected_template or not os.path.exists(f"{TEMPLATE_DIR}/{selected_template}.txt"):
            st.error("Template not found. Please create it or select manually.")
            st.stop()

        template_text = load_template(f"{selected_template}.txt")

        main_prompt = f"You are a radiologist assistant. Use the following template and findings to generate a clean, logical radiology report. Remove normal lines that conflict with the findings. Do not invent findings. Add a smart impression at the end.\n\nTEMPLATE:\n{template_text}\n\nFINDINGS:\n{findings}"

        with st.spinner("Generating report..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": main_prompt}]
            )
            final_report = res.choices[0].message.content
            st.text_area("Final Report", final_report, height=500)
            st.download_button("Copy to Clipboard", final_report, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")
