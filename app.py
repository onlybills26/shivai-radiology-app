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
import requests
import time

# --- Config ---
st.set_page_config(page_title="ShivAI Radiology", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Template Source ---
EMBEDDED_TEMPLATES = {
    "CT Abdomen": "Type of Study: CT Abdomen and Pelvis\nHistory:\nFindings:\n- Liver: Normal.\n- Gallbladder: No stones.\n- Pancreas: Normal.\n- Spleen: Normal.\n- Kidneys: No hydronephrosis.\nImpression:",
    "CT Chest": "Type of Study: CT Chest\nHistory:\nFindings:\n- Lungs: Clear.\n- Mediastinum: Normal.\n- Pleura: No effusion.\nImpression:",
    "MRI Brain": "Type of Study: MRI Brain\nHistory:\nFindings:\n- No acute infarct.\n- No mass lesion.\nImpression:",
    "Ultrasound Abdomen": "Type of Study: Ultrasound Abdomen\nHistory:\nFindings:\n- Liver: Normal echotexture.\n- Gallbladder: No stones.\n- CBD: Not dilated.\nImpression:",
    "Ultrasound Pelvis": "Type of Study: Ultrasound Pelvis (Female)\nHistory:\nFindings:\n- Uterus: Normal size and echotexture.\n- Ovaries: Normal.\nImpression:",
    "CT Brain": "Type of Study: CT Brain (Non-contrast)\nHistory:\nFindings:\n- No acute intracranial hemorrhage.\n- Ventricles: Normal in size.\n- No midline shift.\nImpression:",
    "CT Neck": "Type of Study: CT Neck\nHistory:\nFindings:\n- No mass or lymphadenopathy.\n- Airway patent.\n- Carotid spaces normal.\nImpression:",
    "CT Angiogram – Brain and Neck": "Type of Study: CT Angiogram – Brain and Neck\nHistory:\nFindings:\n- Arteries opacify well.\n- No aneurysm or stenosis.\nImpression:",
    "CT Spine": "Type of Study: CT Spine\nHistory:\nFindings:\n- No acute bony abnormality.\n- Disc spaces preserved.\nImpression:",
    "CT Lower Limb Angiogram": "Type of Study: CT Lower Limb Angiogram\nHistory:\nFindings:\n- Arterial tree opacified.\n- No stenosis or occlusion.\nImpression:",
    "US Renal Doppler": "Type of Study: Ultrasound Renal Doppler\nHistory:\nFindings:\n- Normal renal size.\n- Resistive indices within normal limits.\nImpression:",
    "US Carotid Doppler": "Type of Study: Ultrasound Carotid Doppler\nHistory:\nFindings:\n- Common and internal carotid arteries evaluated.\n- No significant stenosis by NASCET criteria.\nImpression:",
    "MRCP": "Type of Study: MRCP\nHistory:\nFindings:\n- Biliary tree: No dilation.\n- Pancreatic duct: Normal caliber.\nImpression:",
    "MRI Rectum": "Type of Study: MRI Rectum\nHistory:\nFindings:\n- Rectal wall: No thickening or mass.\n- Mesorectum: Intact.\nImpression:",
    "MRI Anal Fistula": "Type of Study: MRI Anal Fistula\nHistory:\nFindings:\n- Inter-sphincteric track noted.\n- No abscess.\nImpression:",
    "MR Enterogram": "Type of Study: MR Enterogram\nHistory:\nFindings:\n- Small bowel: No wall thickening or enhancement.\n- No stricture or fistula.\nImpression:"
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
        "kidney": "Ultrasound Abdomen",
        "rectum": "MRI Rectum",
        "ileum": "MR Enterogram",
        "anal": "MRI Anal Fistula",
        "carotid": "US Carotid Doppler",
        "renal artery": "US Renal Doppler",
        "spine": "CT Spine",
        "circle of willis": "CT Angiogram – Brain and Neck"
    }
    for word, template in keywords.items():
        if word in text.lower():
            return template
    return None
