import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import base64
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from xhtml2pdf import pisa
import plotly.express as px
from PIL import Image

try:
    import fitz  # PyMuPDF — converte páginas de PDF em imagem
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="M e Lopes | ERP Financeiro",
    layout="wide",
    page_icon="💼"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e2e8f0;
        padding: 18px 20px; border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stForm"] {
        background: #f8fafc; padding: 20px;
        border-radius: 12px; border: 1px solid #e2e8f0;
    }
    .header-title { font-size: 26px; font-weight: 700; color: #0f172a; margin: 0; }
    .sub-title    { font-size: 13px; color: #64748b; margin: 2px 0 16px 0; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BANCO DE DADOS (SQLite — Persistente)
# ==========================================
DB_PATH = "erp_melopes.db"

CATEGORIAS = ["Combustível", "Alimentação", "Viagem", "Material",
              "Mão de Obra", "Equipamento", "Outros"]

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nome     TEXT UNIQUE NOT NULL,
                documento TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS despesas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                responsavel TEXT NOT NULL,
                data        TEXT,
                fornecedor  TEXT,
                objeto      TEXT,
                valor       REAL DEFAULT 0,
                categoria   TEXT,
                criado_em   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Clientes padrão
        conn.execute("INSERT OR IGNORE INTO clientes (nome, documento) VALUES (?,?)",
                     ("Wellington Rafael", "014.565.671-36"))
        conn.execute("INSERT OR IGNORE INTO clientes (nome, documento) VALUES (?,?)",
                     ("G.A Solar", "66.283.560/0001-09"))

init_db()

# ---- CRUD helpers ----

def get_clientes() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT nome, documento FROM clientes ORDER BY nome", conn)
    return dict(zip(df["nome"], df["documento"]))


def add_cliente(nome: str, documento: str) -> bool:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO clientes (nome, documento) VALUES (?,?)", (nome, documento))
        return True
    except sqlite3.IntegrityError:
        return False


def get_despesas(responsavel: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(
            """SELECT id,
                      data        AS Data,
                      fornecedor  AS Fornecedor,
                      objeto      AS Objeto,
                      valor       AS Valor,
                      categoria   AS Categoria
               FROM despesas
               WHERE responsavel = ?
               ORDER BY data""",
            conn, params=(responsavel,)
        )
    if df.empty:
        return pd.DataFrame(columns=["id", "Data", "Fornecedor", "Objeto", "Valor", "Categoria"])
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    return df


def add_despesa(responsavel, data, fornecedor, objeto, valor, categoria):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO despesas (responsavel,data,fornecedor,objeto,valor,categoria) VALUES (?,?,?,?,?,?)",
            (responsavel, str(data), fornecedor, objeto, float(valor), categoria)
        )


def delete_des
