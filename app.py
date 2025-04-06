
# ------------------------------------------------------------------------------
# ShivAI Radiology Reporting App
# © 2024 onlybills26@gmail.com - All Rights Reserved
# This software is proprietary and confidential.
# Unauthorized use, reproduction, distribution, or modification is strictly prohibited.
# Commercial use or resale is not allowed without explicit written permission from the author.
# ------------------------------------------------------------------------------

import streamlit as st
import openai
import os
from datetime import datetime

st.set_page_config(page_title="ShivAI Radiology", layout="wide")

# Load API Key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

TEMPLATE_DIR = "templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

BASELINE_TEMPLATES = {
    "CT Abdomen": "Type of Study: CT Abdomen and Pelvis\nHistory:\nFindings:\nImpression:",
    "CT Chest": "Type of Study: CT Chest\nHistory:\nFindings:\nImpression:",
    "MRI Brain": "Type of Study: MRI Brain\nHistory:\nFindings:\nImpression:",
    "Ultrasound Abdomen": "Type of Study: Ultrasound Abdomen\nHistory:\nFindings:\nImpression:",
    "Ultrasound Pelvis": "Type of Study: Ultrasound Pelvis (Female)\nHistory:\nFindings:\nImpression:",
    "MRCP": "Type of Study: MRCP\nHistory:\nFindings:\nImpression:",
    "Thyroid Ultrasound (TI-RADS)": "Type of Study: Ultrasound Thyroid (TI-RADS)\nHistory:\nFindings:\nImpression:",
    "Breast Ultrasound (BI-RADS)": "Type of Study: Ultrasound Breast (BI-RADS)\nHistory:\nFindings:\nImpression:",
    "Liver CT (LI-RADS)": "Type of Study: CT Liver (LI-RADS)\nHistory:\nFindings:\nImpression:",
    "Prostate MRI (PI-RADS)": "Type of Study: MRI Prostate (PI-RADS)\nHistory:\nFindings:\nImpression:"
}

def list_templates():
    return [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".txt")]

def load_template(name):
    local_path = os.path.join(TEMPLATE_DIR, f"{name}.txt")
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            return f.read()
    if name in BASELINE_TEMPLATES:
        return BASELINE_TEMPLATES[name]
    return None

def detect_template_from_findings(text):
    keywords = {
        "liver": "CT Abdomen",
        "thyroid": "Thyroid Ultrasound (TI-RADS)",
        "breast": "Breast Ultrasound (BI-RADS)",
        "lung nodule": "CT Chest",
        "prostate": "Prostate MRI (PI-RADS)",
        "biliary": "MRCP",
        "brain": "MRI Brain",
        "pelvis": "Ultrasound Pelvis",
    }
    for keyword, template in keywords.items():
        if keyword in text.lower():
            return template
    return None

# Sidebar - Template Management
st.sidebar.title("Templates")
template_action = st.sidebar.radio("Template Action", ["Use Template", "Add Template", "Edit Template", "Delete Template"])

if template_action == "Add Template":
    name = st.sidebar.text_input("New Template Name")
    content = st.sidebar.text_area("Template Content")
    if st.sidebar.button("Save"):
        with open(os.path.join(TEMPLATE_DIR, f"{name}.txt"), "w") as f:
            f.write(content)
        st.sidebar.success("Template saved.")

elif template_action == "Edit Template":
    selected = st.sidebar.selectbox("Select Template", list_templates())
    if selected:
        with open(os.path.join(TEMPLATE_DIR, selected), "r") as f:
            content = f.read()
        edited = st.sidebar.text_area("Edit Template", value=content)
        if st.sidebar.button("Update Template"):
            with open(os.path.join(TEMPLATE_DIR, selected), "w") as f:
                f.write(edited)
            st.sidebar.success("Template updated.")

elif template_action == "Delete Template":
    selected = st.sidebar.selectbox("Template to Delete", list_templates())
    if selected and st.sidebar.button("Delete"):
        os.remove(os.path.join(TEMPLATE_DIR, selected))
        st.sidebar.warning("Template deleted.")

# --- Main App UI ---
st.title("ShivAI Radiology Reporting Assistant")

mode = st.radio("Choose Mode", ["Dictate/Type Findings", "Compare Reports"])

auto_detect = st.checkbox("Auto-detect Template", value=True)
show_changes = st.checkbox("Show Changes")

if mode == "Compare Reports":
    st.subheader("Current Report")
    current = st.text_area("Paste current report")
    st.subheader("Prior Report(s)")
    prior = st.text_area("Paste one or more prior reports")

    if st.button("Compare & Generate Impression"):
        prompt = f"You are a radiologist. Compare the current report below to the prior ones and summarize only significant changes. Ignore irrelevant findings like osteophytes or vascular calcification.\n\nCURRENT REPORT:\n{current}\n\nPRIOR REPORTS:\n{prior}"
        with st.spinner("Generating comparative impression..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            output = res.choices[0].message.content
            st.text_area("Comparative Impression", output, height=300)

else:
    findings = st.text_area("Key Findings or Dictation")

    selected_template = None
    if not auto_detect:
        selected_template = st.selectbox("Select Template", list_templates())
    else:
        detected = detect_template_from_findings(findings)
        st.markdown(f"**Auto-Detected Template:** {detected or 'None'}")
        selected_template = detected

    if st.button("Generate Report"):
        template = load_template(selected_template)
        if not template:
            st.warning(f"Template '{selected_template}' not found. Please create it or select manually.")
            st.stop()

        prompt = f"You are a radiologist assistant. Insert the following findings into the report template below. Remove any conflicting normal lines. Tidy the result. Always include structured impression.\n\nTEMPLATE:\n{template}\n\nFINDINGS:\n{findings}"
        with st.spinner("Generating Report..."):
            res = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            final = res.choices[0].message.content
            st.text_area("Final Report", final, height=500)
            st.download_button("Copy to Clipboard", final)

# Footer
st.markdown("---")
st.markdown("© 2024 ShivAI | All Rights Reserved. Unauthorized use or resale prohibited. Contact onlybills26@gmail.com")
