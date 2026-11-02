
"""
LeafCare AI — Plant Disease Detection Dashboard
================================================
Streamlit frontend for the Leaf Disease Detection API.

Backend:
    FastAPI — http://127.0.0.1:8000

Detection endpoint:
    POST /disease-detection-file
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
import json
import os
import textwrap
import hashlib
from datetime import datetime
from io import BytesIO

import requests
import streamlit as st
from PIL import Image, UnidentifiedImageError


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="LeafCare AI | Plant Health Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# 2. APPLICATION CONFIGURATION
# ============================================================

API_URL = os.getenv(
    "LEAF_DISEASE_API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

DETECTION_ENDPOINT = f"{API_URL}/disease-detection-file"

MAX_FILE_SIZE = 10 * 1024 * 1024
REQUEST_TIMEOUT = (5, 120)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


# ============================================================
# 3. CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    
/* ==========================================
   LEAFCARE AI — PREMIUM FOREST GREEN THEME
   ========================================== */

/* Global application */
.stApp {
    background: #F5F7F2;
    color: #20382A;
}

.main .block-container {
    max-width: 1440px;
    padding: 0.7rem 2.5rem 3rem;
    margin-top: 0;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* Typography */
h1, h2, h3, h4 {
    color: #173F2B;
    font-weight: 750;
    letter-spacing: -0.4px;
}

p, label {
    color: #5F7165;
}

/* Main hero */
.hero {
    background: linear-gradient(120deg, #103C29 0%, #1C6040 58%, #347D50 100%);
    padding: 44px 48px;
    border-radius: 24px;
    color: #FFFFFF;
    margin-bottom: 26px;
    box-shadow: 0 14px 35px rgba(20, 65, 42, 0.13);
    position: relative;
    overflow: hidden;
}

.hero-label {
    color: #C7E8D1;
    font-size: 12px;
    font-weight: 750;
    letter-spacing: 2.2px;
    text-transform: uppercase;
    margin-bottom: 13px;
}

.hero-title {
    color: #FFFFFF !important;
    font-size: 44px;
    font-weight: 850;
    line-height: 1.15;
    margin: 0;
}

.hero-description {
    color: #E2F0E5 !important;
    font-size: 16px;
    line-height: 1.8;
    max-width: 720px;
    margin-top: 15px;
    margin-bottom: 0;
}

.hero-tag {
    display: inline-block;
    margin-top: 22px;
    margin-right: 8px;
    padding: 8px 14px;
    border-radius: 30px;
    background: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 700;
    border: 1px solid rgba(255, 255, 255, 0.22);
}

/* Workspace headings */
.section-heading {
    color: #173F2B;
    font-size: 23px;
    font-weight: 800;
    margin-top: 10px;
    margin-bottom: 6px;
}

.section-description {
    color: #758379;
    font-size: 14px;
    margin-bottom: 22px;
}

/* Cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E3EAE1;
    border-radius: 19px;
    padding: 12px;
    box-shadow: 0 5px 20px rgba(25, 65, 42, 0.045);
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #C9DCCB;
    box-shadow: 0 8px 25px rgba(25, 65, 42, 0.075);
}

div[data-testid="stVerticalBlockBorderWrapper"] h3 {
    font-size: 1.3rem !important;
    line-height: 1.4 !important;
    margin-bottom: 0.8rem !important;
    overflow-wrap: normal;
    word-break: normal;
}

/* Metrics */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E3EAE1;
    border-radius: 16px;
    padding: 20px;
    min-height: 112px;
    box-shadow: 0 4px 14px rgba(25, 65, 42, 0.04);
}

.metric-label {
    color: #758379;
    font-size: 12px;
    font-weight: 650;
    margin-bottom: 9px;
}

.metric-value {
    color: #1B603A;
    font-size: 27px;
    font-weight: 850;
}

/* Upload area */
[data-testid="stFileUploader"] {
    background: #F8FAF6;
    border: 1px dashed #A9C9AE;
    border-radius: 15px;
    padding: 14px;
}

[data-testid="stFileUploader"] section {
    border-radius: 12px;
}

/* Preview image */
[data-testid="stImage"] img {
    border-radius: 14px;
    object-fit: contain;
}

/* Buttons */
.stButton > button {
    background: #236C43 !important;
    color: #FFFFFF !important;
    border: 1px solid #236C43 !important;
    border-radius: 12px !important;
    min-height: 47px;
    font-weight: 750 !important;
    transition: all 0.2s ease;
}

.stButton > button:hover:enabled {
    background: #174F32 !important;
    border-color: #174F32 !important;
    color: #FFFFFF !important;
    box-shadow: 0 5px 14px rgba(25, 85, 50, 0.18);
    transform: translateY(-1px);
}

.stButton > button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.stDownloadButton > button {
    border-radius: 11px !important;
    min-height: 43px;
    font-weight: 700;
}

/* Result banners */
.result-banner {
    padding: 23px;
    border-radius: 17px;
    margin: 10px 0 20px;
    border: 1px solid #D6E7D8;
    background: #EFF7EF;
}

.result-banner.disease {
    background: #FFF7EC;
    border-color: #F0DCC0;
}

.result-banner.invalid {
    background: #FFF3F1;
    border-color: #EFD4CE;
}

.result-label {
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 1.2px;
    color: #65776A;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.result-name {
    font-size: 26px;
    font-weight: 850;
    color: #205B36;
    margin: 0;
}

.result-banner.disease .result-name {
    color: #96551B;
}

.result-banner.invalid .result-name {
    color: #A53D32;
}

.result-subtitle {
    color: #65756A;
    font-size: 14px;
    margin-top: 8px;
    margin-bottom: 0;
}

/* Information tags */
.info-tag {
    display: inline-block;
    padding: 7px 13px;
    margin: 3px 5px 3px 0;
    border-radius: 30px;
    background: #EAF3EA;
    color: #28623D;
    font-size: 12px;
    font-weight: 700;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background-color: #2E8751;
}

/* Footer */
.footer {
    text-align: center;
    color: #89958C;
    font-size: 12px;
    padding-top: 28px;
    margin-top: 38px;
    border-top: 1px solid #E2EAE2;
}

/* Responsive layout */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem 0.8rem 2rem;
    }

    .hero {
        padding: 28px 23px;
        border-radius: 18px;
    }

    .hero-title {
        font-size: 32px;
    }

    .hero-description {
        font-size: 14px;
    }

    .sectiocoln-heading {
        font-size: 20px;
    }
}

/* ==========================================
   PREMIUM AGRICULTURAL INSIGHT CARDS
   ========================================== */

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E0E9DF;
    border-radius: 18px;
    box-shadow: 0 5px 18px rgba(25, 65, 42, 0.045);
    transition: all 0.2s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #B9D5BE;
    box-shadow: 0 9px 25px rgba(25, 65, 42, 0.09);
}

/* Insight card headings */
div[data-testid="stVerticalBlockBorderWrapper"] h3 {
    color: #1B5033;
    font-size: 1.2rem !important;
    font-weight: 750 !important;
    margin-bottom: 14px !important;
}

/* Improve insight list readability */
div[data-testid="stVerticalBlockBorderWrapper"] li {
    color: #354C3C;
    line-height: 1.75;
    padding-bottom: 8px;
}

/* Timestamp */
div[data-testid="stCaptionContainer"] {
    color: #829087;
    font-size: 12px;
}


/* ==========================================
   LEAFCARE AI — PREMIUM NAVIGATION
   ========================================== */

.leafcare-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    padding: 12px 24px;
    margin-top: 0;
    margin-bottom: 18px;
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid #E1EAE1;
    border-radius: 16px;
    box-shadow: 0 4px 16px rgba(25, 65, 42, 0.05);
}

.leafcare-brand {
    color: #174B30 !important;
    font-size: 21px;
    font-weight: 850;
    text-decoration: none !important;
    white-space: nowrap;
}

.leafcare-nav-links {
    display: flex;
    align-items: center;
    gap: 28px;
    flex-wrap: wrap;
}

.leafcare-nav-links a {
    color: #52685A !important;
    text-decoration: none !important;
    font-size: 13px;
    font-weight: 650;
    transition: color 0.2s ease;
}

.leafcare-nav-links a:hover {
    color: #237447 !important;
}

@media (max-width: 768px) {
    .leafcare-nav {
        align-items: flex-start;
        flex-direction: column;
        gap: 14px;
    }

    .leafcare-nav-links {
        gap: 15px;
    }
}

/* ABOUT SECTION */
.about-card {
    background: linear-gradient(120deg, #EDF5EC, #FFFFFF);
    border: 1px solid #DCE9DC;
    border-radius: 18px;
    padding: 30px;
    margin: 15px 0 30px;
    box-shadow: 0 5px 18px rgba(25, 65, 42, 0.04);
}

.about-card h3 {
    color: #1B5033;
    font-size: 22px;
    margin-bottom: 14px;
}

.about-card p {
    color: #5F7165;
    line-height: 1.8;
}

.about-tags span {
    display: inline-block;
    background: #E1EFE2;
    color: #236C43;
    padding: 8px 13px;
    border-radius: 25px;
    margin: 8px 7px 0 0;
    font-size: 12px;
    font-weight: 700;
}

/* ==========================================
   HOW IT WORKS — PREMIUM STEP CARDS
   ========================================== */

div[data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

div[data-testid="stHorizontalBlock"] > div {
    display: flex;
    flex-direction: column;
}

div[data-testid="stHorizontalBlock"] 
[data-testid="stVerticalBlockBorderWrapper"] {
    height: 100%;
    min-height: 185px;
    background: linear-gradient(145deg, #FFFFFF, #F1F7F0);
    border: 1px solid #DCE8DC;
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 5px 16px rgba(25, 65, 42, 0.045);
    transition: all 0.25s ease;
}

div[data-testid="stHorizontalBlock"] 
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-4px);
    border-color: #A9CBAE;
    box-shadow: 0 12px 26px rgba(25, 65, 42, 0.10);
}

/* =============================================
   LEAFCARE AI — PREMIUM DESIGN SYSTEM V2
   Forest Green | Ivory | Sage
   ============================================= */

:root {
    --leaf-primary: #216641;
    --leaf-dark: #123D29;
    --leaf-deep: #0D3423;
    --leaf-accent: #79A985;
    --leaf-sage: #EAF3E9;
    --leaf-ivory: #F6F8F3;
    --leaf-border: #DCE7DC;
    --leaf-text: #20392B;
    --leaf-muted: #718276;
    --leaf-shadow: 0 8px 28px rgba(24, 65, 40, 0.065);
}

/* GLOBAL BACKGROUND */

.stApp {
    background: var(--leaf-ivory) !important;
    color: var(--leaf-text);
}

.main .block-container {
    max-width: 1440px;
    padding: 1rem 2.5rem 3.5rem;
}

/* GLOBAL HEADINGS */

h1, h2, h3, h4 {
    color: var(--leaf-dark);
    letter-spacing: -0.5px;
}

h2 {
    font-weight: 800 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 1rem !important;
}

p {
    line-height: 1.75;
}

/* NAVIGATION */

.leafcare-nav {
    background: rgba(255,255,255,0.96);
    border: 1px solid var(--leaf-border);
    border-radius: 18px;
    padding: 15px 25px;
    margin-bottom: 25px;
    box-shadow: var(--leaf-shadow);
    backdrop-filter: blur(12px);
}

.leafcare-brand {
    color: var(--leaf-dark) !important;
    font-size: 22px;
    font-weight: 850;
}

.leafcare-nav-links a {
    color: #52685A !important;
    font-weight: 650;
    transition: color 0.2s ease;
}

.leafcare-nav-links a:hover {
    color: var(--leaf-primary) !important;
}

/* HERO */

.hero {
    background:
        radial-gradient(
            circle at 90% 15%,
            rgba(130, 190, 140, 0.22),
            transparent 35%
        ),
        linear-gradient(
            125deg,
            #103B29 0%,
            #1B6040 55%,
            #347C50 100%
        );
    border-radius: 25px;
    padding: 48px 52px;
    margin-bottom: 35px;
    box-shadow: 0 16px 38px rgba(17, 65, 40, 0.16);
}

.hero-title {
    font-size: 46px !important;
    letter-spacing: -1.5px;
}

.hero-description {
    max-width: 760px;
    line-height: 1.9;
}

.hero-tag {
    border-radius: 30px;
    padding: 9px 16px;
    background: rgba(255,255,255,0.13);
    border: 1px solid rgba(255,255,255,0.24);
}

/* ALL BORDERED CARDS */

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1px solid var(--leaf-border) !important;
    border-radius: 19px !important;
    box-shadow: 0 4px 18px rgba(25, 65, 42, 0.035);
    padding: 16px !important;
    transition:
        transform 0.22s ease,
        box-shadow 0.22s ease,
        border-color 0.22s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #B9D3BD !important;
    box-shadow: 0 10px 28px rgba(25, 65, 42, 0.085);
    transform: translateY(-2px);
}

/* UPLOAD AND PREVIEW */

[data-testid="stFileUploader"] {
    background: #F7FAF6;
    border: 1px dashed #A9C9AE;
    border-radius: 16px;
    padding: 15px;
}

[data-testid="stImage"] img {
    border-radius: 15px;
}

[data-testid="stFileUploader"] button {
    border-radius: 10px;
}

/* BUTTONS */

.stButton > button {
    background: linear-gradient(120deg, #267448, #1A5D39) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    min-height: 48px;
    font-weight: 750 !important;
    box-shadow: 0 4px 12px rgba(31, 104, 64, 0.12);
    transition: all 0.2s ease;
}

.stButton > button:hover:enabled {
    background: linear-gradient(120deg, #185A35, #103F28) !important;
    transform: translateY(-2px);
    box-shadow: 0 7px 17px rgba(31, 104, 64, 0.20);
}

.stDownloadButton > button {
    background: #EDF5ED !important;
    color: #205C37 !important;
    border: 1px solid #D2E4D3 !important;
    border-radius: 12px !important;
    font-weight: 700;
}

/* DISEASE STATUS */

.result-banner {
    background: linear-gradient(120deg, #EDF7ED, #FFFFFF);
    border: 1px solid #CFE3D0;
    border-radius: 19px;
    padding: 25px;
    box-shadow: var(--leaf-shadow);
}

.result-banner.disease {
    background: linear-gradient(120deg, #FFF5E8, #FFFFFF);
    border-color: #F0D9B9;
}

.result-banner.invalid {
    background: linear-gradient(120deg, #FFF0ED, #FFFFFF);
    border-color: #EFD2CB;
}

/* METRIC CARDS */

.metric-card {
    background: linear-gradient(145deg, #FFFFFF, #F2F7F1);
    border: 1px solid var(--leaf-border);
    border-radius: 18px;
    padding: 22px;
    box-shadow: var(--leaf-shadow);
}

.metric-label {
    color: var(--leaf-muted);
    letter-spacing: 0.8px;
    font-size: 11px;
    font-weight: 750;
    text-transform: uppercase;
}

.metric-value {
    color: var(--leaf-primary);
    font-size: 29px;
    font-weight: 850;
}

/* INSIGHT CARDS */

div[data-testid="stVerticalBlockBorderWrapper"] h3 {
    color: var(--leaf-dark);
    font-size: 1.2rem !important;
    font-weight: 800 !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] li {
    color: #405748;
    line-height: 1.85;
    padding-bottom: 9px;
}

/* ABOUT SECTION */

.about-card {
    background:
        radial-gradient(
            circle at 100% 0%,
            rgba(166, 203, 165, 0.20),
            transparent 40%
        ),
        linear-gradient(135deg, #EDF5EB, #FFFFFF);
    border: 1px solid var(--leaf-border);
    border-radius: 22px;
    padding: 34px;
    box-shadow: var(--leaf-shadow);
}

.about-card h3 {
    color: var(--leaf-dark);
    font-size: 24px;
}

.about-tags span {
    background: #E3F0E2;
    border: 1px solid #D4E6D4;
    color: #205C37;
    border-radius: 30px;
    padding: 9px 15px;
    font-weight: 700;
}

/* HOW IT WORKS */

div[data-testid="stHorizontalBlock"] {
    gap: 1.25rem;
}

div[data-testid="stHorizontalBlock"] > div {
    min-width: 0;
}

div[data-testid="stHorizontalBlock"]
[data-testid="stVerticalBlockBorderWrapper"] {
    height: 100%;
    min-height: 190px;
    background: linear-gradient(145deg, #FFFFFF, #F0F6EF) !important;
    border-radius: 19px !important;
    padding: 22px !important;
}

div[data-testid="stHorizontalBlock"]
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-4px);
    border-color: #A8CBAE !important;
}

/* PROGRESS BAR */

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #347D50, #83B78C);
    border-radius: 20px;
}

/* FOOTER */

.footer {
    background: #EDF4EC;
    border: 1px solid var(--leaf-border);
    border-radius: 16px;
    padding: 25px;
    margin-top: 45px;
    color: var(--leaf-muted);
    line-height: 1.8;
}

/* TIMESTAMP AND CAPTIONS */

div[data-testid="stCaptionContainer"] {
    color: #87958A;
    font-size: 12px;
}

/* RESPONSIVE DESIGN */

@media (max-width: 768px) {
    .main .block-container {
        padding: 0.7rem 1rem 2rem;
    }

    .hero {
        padding: 28px 23px;
        border-radius: 18px;
    }

    .hero-title {
        font-size: 32px !important;
    }

    .hero-description {
        font-size: 14px;
    }

    .about-card {
        padding: 22px;
    }

    .leafcare-nav {
        padding: 13px 16px;
    }

    .leafcare-nav-links {
        gap: 13px;
    }
}

/* ==========================================
   LEAFCARE AI — LAYOUT & CARD REFINEMENT
   ========================================== */

/* Prevent unexpected horizontal overflow */
* {
    box-sizing: border-box;
}

.main .block-container {
    width: 100%;
    max-width: 1440px;
    margin-left: auto;
    margin-right: auto;
    overflow-x: clip;
}

/* Keep columns within available space */
div[data-testid="stHorizontalBlock"] {
    width: 100%;
    max-width: 100%;
    gap: 1rem;
}

div[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
    max-width: 100%;
}

/* Refined bordered cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    width: 100%;
    max-width: 100%;
    background: linear-gradient(145deg, #FFFFFF, #F7FAF6) !important;
    border: 1px solid #DFE9DE !important;
    border-radius: 20px !important;
    padding: 20px !important;
    box-shadow: 0 5px 20px rgba(24, 65, 40, 0.055);
    transition: box-shadow 0.25s ease, border-color 0.25s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #B8D3BC !important;
    box-shadow: 0 10px 28px rgba(24, 65, 40, 0.10);
}

/* Better section spacing */
#about,
#how-it-works,
#disease-detection,
#home {
    scroll-margin-top: 24px;
}

#about,
#how-it-works {
    display: block;
    margin-bottom: 12px;
}

/* About section */
.about-card {
    width: 100%;
    max-width: 100%;
    border-radius: 22px;
    padding: 34px;
    background: linear-gradient(135deg, #EAF4E9, #FFFFFF);
    border: 1px solid #D9E8D9;
    box-shadow: 0 8px 25px rgba(24, 65, 40, 0.055);
}

/* Consistent section headings */
.section-heading {
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 12px;
}

/* Responsive cards */
@media (max-width: 768px) {
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 15px !important;
        border-radius: 16px !important;
    }

    .about-card {
        padding: 22px;
    }
}

/* ==========================================
   LEAFCARE AI — ABOUT & PROCESS REDESIGN
   ========================================== */

/* ABOUT SECTION */
.about-section {
    position: relative;
    display: grid;
    grid-template-columns: 1.35fr 0.75fr;
    gap: 28px;
    align-items: stretch;
    padding: 34px;
    margin: 16px 0 55px;
    border: 1px solid #DCE8DA;
    border-radius: 24px;
    background: linear-gradient(125deg, #EDF5EA 0%, #FFFFFF 75%);
    box-shadow: 0 12px 32px rgba(24, 65, 40, 0.055);
    overflow: hidden;
}

.about-content {
    position: relative;
    z-index: 1;
}

.about-eyebrow {
    color: #398052;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
}

.about-title {
    color: #153F2A;
    font-size: 29px;
    line-height: 1.3;
    font-weight: 850;
    letter-spacing: -0.8px;
    margin: 0 0 18px;
}

.about-description {
    color: #607267;
    font-size: 15px;
    line-height: 1.9;
    margin-bottom: 13px;
}

.about-feature-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 24px;
}

.about-feature {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: #E3F0E2;
    border: 1px solid #D2E5D2;
    color: #245D39;
    padding: 10px 14px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 750;
}

.about-visual {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    min-height: 230px;
    padding: 25px;
    border-radius: 20px;
    background:
        radial-gradient(circle at 50% 35%, #D5EBD4, transparent 65%),
        linear-gradient(145deg, #E6F1E4, #F7FAF5);
    border: 1px solid #DCE9D9;
}

.about-visual-icon {
    font-size: 76px;
    line-height: 1.3;
    margin-bottom: 13px;
}

.about-visual-title {
    color: #1A5433;
    font-size: 18px;
    font-weight: 800;
}

.about-visual-text {
    color: #75867A;
    font-size: 12px;
    line-height: 1.7;
    max-width: 230px;
    margin-top: 8px;
}

/* SECTION INTRO */
.process-intro {
    color: #77867B;
    font-size: 14px;
    margin-top: -8px;
    margin-bottom: 25px;
}

/* HOW IT WORKS */
.process-card {
    position: relative;
    height: 100%;
    min-height: 255px;
    padding: 25px 23px;
    border: 1px solid #DFE9DD;
    border-radius: 21px;
    background: linear-gradient(145deg, #FFFFFF, #F5F9F3);
    box-shadow: 0 7px 22px rgba(24, 65, 40, 0.045);
    transition: transform 0.25s ease,
                box-shadow 0.25s ease,
                border-color 0.25s ease;
    overflow: hidden;
}

.process-card:hover {
    transform: translateY(-6px);
    border-color: #AFCDAF;
    box-shadow: 0 15px 30px rgba(24, 65, 40, 0.10);
}

.process-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 28px;
}

.process-number {
    color: #C5D9C5;
    font-size: 37px;
    line-height: 1;
    font-weight: 850;
    letter-spacing: -1px;
}

.process-icon {
    width: 52px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 15px;
    background: #E7F2E5;
    border: 1px solid #D9E9D7;
    font-size: 25px;
}

.process-card h3 {
    color: #19452E;
    font-size: 20px;
    font-weight: 800;
    margin: 0 0 12px;
}

.process-card p {
    color: #718076;
    font-size: 14px;
    line-height: 1.8;
    margin: 0;
}

.process-label {
    display: inline-block;
    margin-top: 22px;
    padding: 7px 11px;
    background: #EAF3E8;
    color: #34734A;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.7px;
    text-transform: uppercase;
}

/* Responsive layout */
@media (max-width: 850px) {
    .about-section {
        grid-template-columns: 1fr;
        padding: 24px;
    }

    .about-visual {
        min-height: 190px;
    }
}

@media (max-width: 768px) {
    .about-title {
        font-size: 24px;
    }

    .process-card {
        min-height: auto;
        padding: 22px;
    }

    .process-number {
        font-size: 31px;
    }
}

/* ==========================================
   FINAL TYPOGRAPHY & CARD POLISH
   ========================================== */

/* About section */
.about-section {
    padding: 42px !important;
    gap: 35px !important;
    margin-bottom: 65px !important;
}

.about-eyebrow {
    font-size: 12px !important;
    margin-bottom: 18px !important;
}

.about-title {
    font-size: 34px !important;
    line-height: 1.35 !important;
    margin-bottom: 22px !important;
}

.about-description {
    font-size: 16px !important;
    line-height: 1.9 !important;
    max-width: 720px;
    margin-bottom: 17px !important;
}

.about-feature {
    padding: 11px 16px !important;
    font-size: 13px !important;
}

.about-visual {
    min-height: 260px !important;
    border-radius: 22px !important;
}

.about-visual-icon {
    font-size: 88px !important;
}

.about-visual-title {
    font-size: 21px !important;
}

.about-visual-text {
    font-size: 14px !important;
    line-height: 1.8 !important;
}

/* How It Works heading */
.process-intro {
    font-size: 15px !important;
    margin-bottom: 28px !important;
}

/* Process cards */
.process-card {
    min-height: 285px !important;
    padding: 30px !important;
    border-radius: 22px !important;
}

.process-top {
    margin-bottom: 35px !important;
}

.process-number {
    font-size: 46px !important;
}

.process-icon {
    width: 60px !important;
    height: 60px !important;
    font-size: 29px !important;
    border-radius: 18px !important;
}

.process-card h3 {
    font-size: 23px !important;
    margin-bottom: 15px !important;
}

.process-card p {
    font-size: 15px !important;
    line-height: 1.9 !important;
}

.process-label {
    font-size: 11px !important;
    padding: 9px 13px !important;
    margin-top: 24px !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .about-section {
        padding: 24px !important;
    }

    .about-title {
        font-size: 27px !important;
    }

    .process-card {
        min-height: 240px !important;
    }
}


/* ==========================================
   LEAFCARE AI — PREMIUM CARD DESIGN
========================================== */

/* Global section spacing */
section.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2.5rem;
}

/* Main bordered cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(
        145deg,
        #FFFFFF 0%,
        #F5F9F4 100%
    ) !important;

    border: 1px solid #DCE9DC !important;
    border-radius: 18px !important;

    box-shadow: 0 5px 18px rgba(24, 75, 48, 0.055);

    transition:
        transform 0.25s ease,
        box-shadow 0.25s ease,
        border-color 0.25s ease;
}

/* Hover effect */
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #A9CDB0 !important;
    box-shadow: 0 10px 26px rgba(24, 75, 48, 0.10);
}

/* Report heading */
.report-heading {
    padding: 12px 0 18px;
    margin-bottom: 8px;
}

.report-heading h2 {
    color: #123F2D;
    font-size: 1.8rem;
    font-weight: 750;
    margin: 8px 0;
    letter-spacing: -0.5px;
}

.report-heading p {
    color: #718477;
    font-size: 0.95rem;
    margin-bottom: 0;
}

.report-eyebrow {
    color: #28784D;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 2px;
}

/* Section headings */
div[data-testid="stMarkdownContainer"] h3 {
    color: #174B35;
    font-weight: 700;
    letter-spacing: -0.3px;
    margin-top: 1.2rem;
}

/* Card headings */
div[data-testid="stMarkdownContainer"] h4 {
    color: #194D36;
    font-weight: 700;
}

/* Metric cards */
div[data-testid="stMetric"] {
    padding: 8px 4px;
}

div[data-testid="stMetricLabel"] {
    color: #819487;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.7px;
}

div[data-testid="stMetricValue"] {
    color: #164A32;
    font-weight: 750;
}

/* Progress bar */
div[data-testid="stProgressBar"] > div {
    background-color: #E4EEE5;
    border-radius: 20px;
}

div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(
        90deg,
        #246B45,
        #65A878
    );
    border-radius: 20px;
}

/* Download button */
div.stDownloadButton > button {
    background: #EDF5ED;
    color: #1B603C;
    border: 1px solid #CFE2D0;
    border-radius: 12px;
    font-weight: 650;
    min-height: 44px;
    transition: all 0.2s ease;
}

div.stDownloadButton > button:hover {
    background: #DCEEDF;
    border-color: #91BD9A;
    color: #12482E;
}

/* Info and status messages */
div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Agricultural insight lists */
div[data-testid="stVerticalBlockBorderWrapper"] ul {
    padding-left: 1.2rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] li {
    color: #365B48;
    line-height: 1.75;
    padding-bottom: 5px;
}

/* Footer */
.footer {
    background: linear-gradient(
        120deg,
        #EAF3E9,
        #F7FAF6
    );
    border: 1px solid #D8E8D8;
    border-radius: 16px;
    padding: 24px;
    margin-top: 28px;
    text-align: center;
    color: #63796A;
    line-height: 1.8;
}

/* Responsive layout */
@media (max-width: 768px) {
    section.main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .report-heading h2 {
        font-size: 1.45rem;
    }
}
/* Refine report typography and vertical spacing */
div[data-testid="stMarkdownContainer"] h2 {
    margin-top: 0.45rem;
    margin-bottom: 0.4rem;
    line-height: 1.3;
}

div[data-testid="stMarkdownContainer"] h4 {
    margin-bottom: 0.35rem;
    letter-spacing: 0.6px;
}

div[data-testid="stCaptionContainer"] {
    color: #829487;
    line-height: 1.5;
}

/* Consistent spacing between report sections */
div[data-testid="stHorizontalBlock"] {
    gap: 1rem;
}

/* ==========================================
   RESPONSIVE NAVIGATION
========================================== */

.leafcare-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
    padding: 16px 24px;
    width: 100%;
    box-sizing: border-box;
}

.leafcare-nav-links {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 12px;
}

.leafcare-nav-links a {
    color: #244B36;
    text-decoration: none;
    font-size: 14px;
    font-weight: 650;
    padding: 10px 14px;
    border-radius: 9px;
    transition: all 0.2s ease;
}

.leafcare-nav-links a:hover {
    color: #17643D;
    background: #EAF4E9;
}

/* Tablet */
@media (max-width: 900px) {
    .leafcare-nav {
        padding: 14px 18px;
    }

    .leafcare-nav-links {
        gap: 6px;
    }

    .leafcare-nav-links a {
        padding: 9px 10px;
        font-size: 13px;
    }
}



/* ==========================================
   COMPLETE MOBILE RESPONSIVE DESIGN
========================================== */

@media (max-width: 600px) {

    /* Navigation */
    .leafcare-nav {
        flex-direction: column;
        align-items: center;
        padding: 14px;
        gap: 12px;
        width: 100%;
        box-sizing: border-box;
    }

    .leafcare-nav-links {
        width: 100%;
        justify-content: center;
        flex-wrap: wrap;
        gap: 6px;
    }

    .leafcare-nav-links a {
        font-size: 12px;
        padding: 8px 10px;
    }

    /* Page spacing */
    [data-testid="stMainBlockContainer"] {
        padding: 1rem !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    /* MOBILE STREAMLIT COLUMN FIX */
div[data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) !important;
    width: 100% !important;
    max-width: 100% !important;
    gap: 16px !important;
    box-sizing: border-box !important;
}

div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    flex: none !important;
    box-sizing: border-box !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

    

    /* Metric labels */
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
    }

    /* Metric values */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
    }

    /* Hero section */
    .hero {
        padding: 26px 18px !important;
        border-radius: 18px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    .hero-title {
        font-size: clamp(2rem, 9vw, 2.7rem) !important;
        line-height: 1.2 !important;
    }

    .hero-description {
        font-size: 1rem !important;
        line-height: 1.7 !important;
    }

    .hero-tag {
        display: inline-flex !important;
        margin: 5px 5px 5px 0 !important;
        white-space: normal !important;
    }

    /* Section headings */
    h1 {
        font-size: 1.8rem !important;
    }

    h2 {
        font-size: 1.5rem !important;
    }

    h3 {
        font-size: 1.25rem !important;
    }

    /* Images */
    div[data-testid="stImage"] img {
        display: block !important;
        width: 100% !important;
        max-width: 100% !important;
        height: auto !important;
        border-radius: 12px !important;
    }
}



    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def safe_list(value):
    """Return a list containing only non-empty strings."""

    if not isinstance(value, list):
        return []

    return [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]


def validate_uploaded_image(file_bytes, filename):
    """Validate the uploaded image before sending it to the API."""

    if not file_bytes:
        return False, "The uploaded file is empty."

    if len(file_bytes) > MAX_FILE_SIZE:
        return False, "Image size must not exceed 10 MB."

    extension = filename.rsplit(".", 1)[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return False, "Only JPG, JPEG and PNG images are supported."

    try:
        with Image.open(BytesIO(file_bytes)) as image:
            if image.format not in {"JPEG", "PNG"}:
                return False, "The file content is not a supported JPEG or PNG image."

            image.verify()

        return True, ""

    except (UnidentifiedImageError, OSError, ValueError):
        return False, "The uploaded file is not a valid image."


def call_detection_api(file_bytes, filename, mime_type):
    """Send an image to the FastAPI disease detection endpoint."""

    files = {
        "file": (
            filename,
            file_bytes,
            mime_type or "application/octet-stream"
        )
    }

    try:
        response = requests.post(
            DETECTION_ENDPOINT,
            files=files,
            timeout=REQUEST_TIMEOUT
        )

        try:
            response_data = response.json()
        except ValueError:
            response_data = {}

        if response.status_code == 200:
            if not isinstance(response_data, dict):
                return None, "The API returned an unexpected response."

            return response_data, None

        detail = response_data.get("detail")

        if not isinstance(detail, str):
            detail = f"API returned HTTP {response.status_code}."

        return None, detail

    except requests.exceptions.Timeout:
        return None, (
            "The analysis request timed out. "
            "Please try again after checking the AI service."
        )

    except requests.exceptions.ConnectionError:
        return None, (
            "Unable to connect to the detection API. "
            "Make sure the FastAPI server is running."
        )

    except requests.exceptions.RequestException as error:
        return None, f"Request failed: {error}"



def create_report(result, filename="LeafCare_Analysis_Report.pdf"):
    """Generate a professionally formatted PDF analysis report."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Brand",
        parent=styles["Title"],
        fontSize=25,
        textColor=colors.HexColor("#237447"),
        alignment=TA_CENTER,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        name="Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#237447"),
        spaceBefore=14,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="BodyCustom",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#26382E")
    ))

    styles.add(ParagraphStyle(
        name="SmallCustom",
        parent=styles["BodyText"],
        fontSize=8,
        textColor=colors.HexColor("#718078")
    ))

    story = []

    def safe(value):
        """Escape text before inserting it into ReportLab paragraphs."""
        from xml.sax.saxutils import escape
        return escape(str(value))

    def add_section(title):
        story.append(Paragraph(safe(title), styles["Section"]))

    def add_list(title, items):
        add_section(title)

        if not items:
            story.append(Paragraph("No information available.", styles["BodyCustom"]))
            return

        for item in items:
            story.append(Paragraph(
                f"&bull; {safe(item)}",
                styles["BodyCustom"]
            ))
            story.append(Spacer(1, 4))

    # Header
    story.append(Paragraph("LeafCare AI", styles["Brand"]))
    story.append(Paragraph(
        "PLANT HEALTH ANALYSIS REPORT",
        ParagraphStyle(
            "Subtitle",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontSize=10,
            textColor=colors.HexColor("#718078")
        )
    ))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(
        width="100%",
        color=colors.HexColor("#237447"),
        thickness=2
    ))
    story.append(Spacer(1, 12))

    # Metadata
    story.append(Paragraph(
        f"<b>Report generated:</b> "
        f"{datetime.now().astimezone().strftime('%d %B %Y, %I:%M %p')}",
        styles["BodyCustom"]
    ))

    story.append(Spacer(1, 12))

    # Analysis summary
    add_section("1. Analysis Summary")

    disease_detected = result.get("disease_detected", False)
    disease_type = result.get("disease_type", "unknown")
    disease_name = result.get("disease_name")

    if disease_type == "invalid_image":
        status = "Invalid Leaf Image"
    elif disease_type == "healthy":
        status = "Healthy Leaf"
    elif disease_detected:
        status = "Disease or Damage Detected"
    else:
        status = "No Disease Detected"

    summary_data = [
        ["Plant Health Status", status],
        ["Detected Condition", disease_name or "None"],
        ["Disease Category", disease_type.title()],
        ["Severity", result.get("severity", "Unknown").title()],
        ["AI-reported Confidence", f"{result.get('confidence', 0)}%"]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[55 * mm, 110 * mm]
    )

    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF4EC")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#26382E")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5E2D8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(summary_table)

    # Agricultural insights
    add_list("2. Observed Symptoms", result.get("symptoms", []))
    add_list("3. Possible Causes", result.get("possible_causes", []))
    add_list("4. Treatment Recommendations", result.get("treatment", []))

    # Disclaimer
    add_section("5. Important Disclaimer")

    story.append(Paragraph(
        "This report contains an AI-generated visual assessment. "
        "The confidence score is a model-reported estimate and is not "
        "independently validated diagnostic accuracy. This report is "
        "not a substitute for laboratory testing or professional "
        "agricultural diagnosis. Consult a qualified agricultural "
        "expert before making significant crop-treatment decisions.",
        styles["BodyCustom"]
    ))

    story.append(Spacer(1, 20))

    story.append(HRFlowable(
        width="100%",
        color=colors.HexColor("#D5E2D8"),
        thickness=0.7
    ))

    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Generated by LeafCare AI | Plant Health Intelligence",
        styles["SmallCustom"]
    ))

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()



# ============================================================
# 5. RESULT DISPLAY
# ============================================================

def display_list_section(title, items, icon):
    """Display a result section using native Streamlit components."""

    st.markdown(f"#### {icon} {title}")

    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption("No information available.")



# 6. RESULT DISPLAY FUNCTION





def display_results(result):
    """Display a polished analysis report for all detection outcomes."""

    if not isinstance(result, dict):
        st.error("Invalid analysis response received.")
        return

    disease_type = result.get("disease_type")
    disease_detected = result.get("disease_detected")
    disease_name = result.get("disease_name")
    confidence = result.get("confidence")
    severity = result.get("severity")
    timestamp = result.get("analysis_timestamp", "Not available")

    symptoms = safe_list(result.get("symptoms"))
    causes = safe_list(result.get("possible_causes"))
    treatments = safe_list(result.get("treatment"))

    valid_confidence = (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and 0 <= confidence <= 100
    )

    # --------------------------------------------
    # REPORT HEADER
    # --------------------------------------------

    st.markdown(
        """
        <div class="report-heading">
            <div>
                <span class="report-eyebrow">PLANT HEALTH ASSESSMENT</span>
                <h2>📊 Analysis Report</h2>
                <p>AI-powered insights for better plant health decisions.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------
    # INVALID IMAGE
    # --------------------------------------------

    if disease_type == "invalid_image":

        st.error("⚠️ Invalid Leaf Image")

        st.write(
            "The AI could not recognize a suitable plant leaf "
            "in the uploaded image."
        )

        st.markdown("### 🔎 Recommended Next Steps")

        col1, col2 = st.columns(2, gap="medium")

        with col1:
            with st.container(border=True):
                display_list_section(
                    "What went wrong",
                    symptoms,
                    "🔎"
                )

        with col2:
            with st.container(border=True):
                display_list_section(
                    "What to do next",
                    treatments,
                    "💡"
                )

        st.info(
            "Please upload a clear photograph of a plant leaf."
        )

    # --------------------------------------------
    # DISEASE DETECTED
    # --------------------------------------------

    elif disease_detected is True:

        display_name = (
            disease_name.strip()
            if isinstance(disease_name, str) and disease_name.strip()
            else "Unspecified disease"
        )

        st.warning("🦠 Disease detected")

        with st.container(border=True):

            st.markdown("#### DETECTED CONDITION")

            st.markdown(f"## {display_name}")

            st.caption(
                "Potential disease indicators identified in the "
                "uploaded leaf image."
            )

        st.markdown("### 📈 Detection Overview")

        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            with st.container(border=True):
                st.caption("DISEASE TYPE")
                st.subheader(str(disease_type or "N/A"))

        with col2:
            with st.container(border=True):
                st.caption("SEVERITY")
                st.subheader(str(severity or "N/A"))

        with col3:
            with st.container(border=True):
                st.caption("CLASSIFICATION CONFIDENCE")
                st.subheader(
                    f"{confidence:.1f}%"
                    if valid_confidence else "N/A"
                )

        if valid_confidence:
            st.caption(
                "Model-reported classification confidence. "
                "This is not independently validated diagnostic accuracy."
            )
            st.progress(float(confidence) / 100)

        # ----------------------------------------
        # AGRICULTURAL INSIGHTS
        # ----------------------------------------

        st.markdown("### 🌿 Agricultural Insights")

        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            with st.container(border=True):
                display_list_section(
                    "Symptoms",
                    symptoms,
                    "🔬"
                )

        with col2:
            with st.container(border=True):
                display_list_section(
                    "Possible Causes",
                    causes,
                    "🌱"
                )

        with col3:
            with st.container(border=True):
                display_list_section(
                    "Treatment Recommendations",
                    treatments,
                    "🧪"
                )

    # --------------------------------------------
    # HEALTHY LEAF
    # --------------------------------------------

    elif disease_detected is False and disease_type == "healthy":

        st.success("✅ Healthy Leaf")

        with st.container(border=True):
            st.markdown("### 🌿 Plant Health Status")
            st.subheader("No disease detected")

            st.write(
                "No disease was detected by the AI model "
                "in the uploaded image."
            )

        if valid_confidence:

            col1, col2 = st.columns(2, gap="medium")

            with col1:
                with st.container(border=True):
                    st.caption("CLASSIFICATION CONFIDENCE")
                    st.subheader(f"{confidence:.1f}%")

            with col2:
                with st.container(border=True):
                    st.caption("PLANT HEALTH STATUS")
                    st.subheader("Healthy")

            st.caption(
                "Model-reported classification confidence. "
                "This is not independently validated diagnostic accuracy."
            )

        st.info(
            "Continue regular plant monitoring and maintain "
            "appropriate watering and nutrient management."
        )

    # --------------------------------------------
    # UNKNOWN RESPONSE
    # --------------------------------------------

    else:

        st.error(
            "The API returned an unrecognized analysis result."
        )

        st.json(result)

    # --------------------------------------------
    # REPORT FOOTER AND DOWNLOAD
    # --------------------------------------------

    st.divider()

    st.caption(f"🕒 Analysis timestamp: {timestamp}")

    st.markdown("### 📄 Export Analysis")

    st.download_button(
    label="⬇️ Download PDF Report",
    data=create_report(result),
    file_name="LeafCare_Analysis_Report.pdf",
    mime="application/pdf",
    width="stretch"
)

# ==========================================
# PREMIUM NAVIGATION BAR
# ==========================================


# ==========================================
# PREMIUM NAVIGATION BAR
# ==========================================

st.markdown(
    """
    <nav class="leafcare-nav">
        <a class="leafcare-brand" href="#home">🌿 LeafCare AI</a>
        <div class="leafcare-nav-links">
            <a href="#home">Home</a>
            <a href="#disease-detection">Disease Detection</a>
            <a href="#about">About</a>
            <a href="#how-it-works">How It Works</a>
        </div>
    </nav>
    """,
    unsafe_allow_html=True
)

st.markdown('<div id="home"></div>', unsafe_allow_html=True)
# ============================================================
# 7. HEADER / HERO SECTION
# ============================================================


st.markdown(
    """
<div class="hero">
<div class="hero-label">PLANT HEALTH INTELLIGENCE PLATFORM</div>
<h1 class="hero-title">LeafCare AI 🌿</h1>
<p class="hero-description">
Intelligent leaf disease detection powered by AI.
Upload a plant leaf image to identify potential diseases,
understand symptoms and explore treatment recommendations.
</p>
<div class="hero-tag">✦ AI-POWERED ANALYSIS</div>
<div class="hero-tag">✦ PLANT HEALTH MONITORING</div>
</div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 8. DASHBOARD INTRODUCTION
# ============================================================

st.markdown(
    '<div class="section-heading">Disease Detection Workspace</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="section-description">
        Upload a clear photograph of a plant leaf to begin AI analysis.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 8. UPLOAD AND PREVIEW
# ============================================================


upload_col, preview_col = st.columns(
    [1.05, 0.95],
    gap="medium"
)

with upload_col:
    with st.container(border=True):
        st.subheader("📤 Upload Leaf Image")

        st.write(
            "Choose a clear leaf photograph from your device."
        )

        uploaded_file = st.file_uploader(
            "Select an image",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False,
            help="Supported formats: JPG, JPEG and PNG. Maximum size: 10 MB."
        )

        # Generate a unique identifier for the uploaded image.
        current_image_hash = None

        if uploaded_file is not None:
            current_image_hash = hashlib.sha256(
                uploaded_file.getvalue()
            ).hexdigest()

        st.caption("Maximum file size: 10 MB")

        analyze_button = st.button(
            "🔍 Analyze Leaf",
            width="stretch",
            disabled=uploaded_file is None
        )

        if uploaded_file is None:
            st.info("Upload a leaf image to enable AI analysis.")

with preview_col:
    with st.container(border=True):
        st.subheader("🖼️ Image Preview")

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()

            is_valid, validation_message = validate_uploaded_image(
                file_bytes,
                uploaded_file.name
            )

            if is_valid:
                st.image(
                    file_bytes,
                    caption=uploaded_file.name,
                    width="stretch"
                )

                st.caption(
                    f"File size: {len(file_bytes) / 1024:.1f} KB"
                )
            else:
                st.error(validation_message)

        else:
            st.markdown(
                """
                <div style="
                    min-height:210px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    flex-direction:column;
                    background:#F5F9F5;
                    border:1px dashed #BDD2C1;
                    border-radius:13px;
                    color:#718276;
                    text-align:center;
                    padding:20px;
                ">
                    <div style="font-size:45px;">🌿</div>
                    <div style="font-size:15px;font-weight:650;">
                        Your image preview will appear here
                    </div>
                    <div style="font-size:12px;margin-top:8px;">
                        Upload a JPG or PNG image to continue
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
st.markdown('<div id="disease-detection"></div>', unsafe_allow_html=True)
# ============================================================
# 9. RUN DISEASE DETECTION
# ============================================================


if uploaded_file is not None and analyze_button:

    # Remove the previous result before processing a new request.
    st.session_state.pop("leafcare_result", None)
    st.session_state.pop("leafcare_filename", None)

    file_bytes = uploaded_file.getvalue()

    is_valid, validation_message = validate_uploaded_image(
        file_bytes,
        uploaded_file.name
    )

    if not is_valid:

        st.error(validation_message)

    else:

        mime_type = (
            "image/png"
            if uploaded_file.name.lower().endswith(".png")
            else "image/jpeg"
        )

        with st.spinner(
            "Analyzing your leaf image... Please wait."
        ):

            result, error = call_detection_api(
                file_bytes,
                uploaded_file.name,
                mime_type
            )

        if error:

            st.error(error)

        elif result is not None:

            st.session_state["leafcare_result"] = result
            st.session_state["leafcare_filename"] = uploaded_file.name
            st.session_state["leafcare_image_hash"] = current_image_hash

            st.success("Image analysis completed successfully.")

        else:

            st.error(
                "No valid response was received from the API."
            )



# ============================================================
# 10. DISPLAY ANALYSIS RESULTS
# ============================================================

if (
    "leafcare_result" in st.session_state
    and st.session_state.get("leafcare_image_hash") == current_image_hash
    and current_image_hash is not None
):

    st.markdown("---")

    st.markdown(
        '<div class="section-heading">Analysis Report</div>',
        unsafe_allow_html=True
    )

    filename = st.session_state.get(
        "leafcare_filename",
        "Uploaded image"
    )

    st.caption(f"Analysis for: {filename}")

    display_results(
        st.session_state["leafcare_result"]
    )




# ==========================================
# ABOUT LEAFCARE AI — PREMIUM SECTION
# ==========================================

st.markdown('<div id="about"></div>', unsafe_allow_html=True)

st.markdown("## 🌿 About LeafCare AI")

st.html("""
<section class="about-section">
    <div class="about-content">

        <div class="about-eyebrow">
            ABOUT OUR PLATFORM
        </div>

        <h2 class="about-title">
            Smarter Plant Health.<br>
            Better Agricultural Decisions.
        </h2>

        <p class="about-description">
            LeafCare AI is an AI-powered plant health assessment
            platform designed to identify potential leaf diseases
            through uploaded images.
        </p>

        <p class="about-description">
            Discover visual symptoms, possible causes and
            treatment recommendations to support more informed
            agricultural decisions.
        </p>

        <div class="about-feature-list">
            <span class="about-feature">✦ AI-Powered Analysis</span>
            <span class="about-feature">✦ Plant Health Insights</span>
            <span class="about-feature">✦ Accessible Technology</span>
        </div>

    </div>

    <div class="about-visual">
        <div class="about-visual-icon">🌿</div>

        <div class="about-visual-title">
            Grow Healthier Plants
        </div>

        <div class="about-visual-text">
            Technology-driven insights for better
            plant health awareness.
        </div>
    </div>
</section>
""")


# ==========================================
# HOW IT WORKS — THREE-STEP PROCESS
# ==========================================

st.markdown(
    '<div id="how-it-works"></div>',
    unsafe_allow_html=True
)

st.markdown("## ⚙️ How It Works")

st.html("""
<div class="process-intro">
    Get meaningful plant health insights in three simple steps.
</div>
""")

step1, step2, step3 = st.columns(3, gap="medium")


# STEP 01 — UPLOAD

with step1:
    st.html("""
    <div class="process-card">
        <div class="process-top">
            <span class="process-number">01</span>
            <div class="process-icon">📷</div>
        </div>

        <h3>Upload Your Leaf</h3>

        <p>
            Select a clear JPG or PNG photograph
            of a plant leaf from your device.
        </p>

        <span class="process-label">Image Upload</span>
    </div>
    """)


# STEP 02 — ANALYZE

with step2:
    st.html("""
    <div class="process-card">
        <div class="process-top">
            <span class="process-number">02</span>
            <div class="process-icon">🤖</div>
        </div>

        <h3>AI Analysis</h3>

        <p>
            Our AI examines the uploaded image
            to identify potential disease indicators.
        </p>

        <span class="process-label">Intelligent Detection</span>
    </div>
    """)


# STEP 03 — DISCOVER

with step3:
    st.html("""
    <div class="process-card">
        <div class="process-top">
            <span class="process-number">03</span>
            <div class="process-icon">🌱</div>
        </div>

        <h3>Discover Insights</h3>

        <p>
            Explore symptoms, possible causes
            and treatment recommendations.
        </p>

        <span class="process-label">Plant Health Insights</span>
    </div>
    """)



# ============================================================
# 11. FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        <strong>LeafCare AI</strong> · Plant Health Intelligence<br>
        AI-generated results are informational and should be
        verified with a qualified agricultural expert.
    </div>
    """,
    unsafe_allow_html=True
)
