import streamlit as st
import pandas as pd
import sqlite3
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px

from datetime import datetime, date
from io import BytesIO
from PIL import Image
from typing import Optional
from weasyprint import HTML

# ==========================================
# CONFIG PAGE
# ==========================================

st.set_page_config(
    page_title="M e Lopes | ERP Financeiro",
    layout="wide",
    page_icon="💼"
)

# ==========================================
# CSS
# ==========================================

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

div[data-testid="stMetric"] {
    background: white;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #e2e8f0;
}

.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE
# ==========================================

DB_PATH = "erp_financeiro.db"

CATEGORIAS = [
    "Combustível",
    "Alimentação",
    "Viagem",
    "Material",
