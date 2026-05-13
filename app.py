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
    "Mão de Obra",
    "Equipamento",
    "Outros"
]


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            documento TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            responsavel TEXT,
            data TEXT,
            fornecedor TEXT,
            objeto TEXT,
            valor REAL,
            categoria TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute(
        "INSERT OR IGNORE INTO clientes(nome, documento) VALUES (?, ?)",
        ("Wellington Rafael", "014.565.671-36")
    )

    conn.commit()
    conn.close()


init_db()

# ==========================================
# CACHE
# ==========================================

@st.cache_data(ttl=60)
def get_clientes():
    conn = get_conn()

    df = pd.read_sql(
        "SELECT nome, documento FROM clientes ORDER BY nome",
        conn
    )

    conn.close()

    return dict(zip(df["nome"], df["documento"]))


@st.cache_data(ttl=30)
def get_despesas(responsavel):
    conn = get_conn()

    df = pd.read_sql(
        """
        SELECT
            id,
            data AS Data,
            fornecedor AS Fornecedor,
            objeto AS Objeto,
            valor AS Valor,
            categoria AS Categoria
        FROM despesas
        WHERE responsavel = ?
        ORDER BY data
        """,
        conn,
        params=(responsavel,)
    )

    conn.close()

    if df.empty:
        return pd.DataFrame(columns=[
            "id",
            "Data",
            "Fornecedor",
            "Objeto",
            "Valor",
            "Categoria"
        ])

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

    return df


# ==========================================
# HELPERS
# ==========================================


def clear_cache():
    st.cache_data.clear()



def formatar_br(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



def add_cliente(nome, documento):
    try:
        conn = get_conn()

        conn.execute(
            "INSERT INTO clientes(nome, documento) VALUES (?, ?)",
            (nome, documento)
        )

        conn.commit()
        conn.close()

        clear_cache()

        return True

    except sqlite3.IntegrityError:
        return False



def add_despesa(responsavel, data, fornecedor, objeto, valor, categoria):
    conn = get_conn()

    conn.execute(
        """
        INSERT INTO despesas(
            responsavel,
            data,
            fornecedor,
            objeto,
            valor,
            categoria
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            responsavel,
            str(data),
            fornecedor,
            objeto,
            float(valor),
            categoria
        )
    )

    conn.commit()
    conn.close()

    clear_cache()



def delete_despesas(ids):
    conn = get_conn()

    conn.executemany(
        "DELETE FROM despesas WHERE id=?",
        [(i,) for i in ids]
    )

    conn.commit()
    conn.close()

    clear_cache()



def import_bulk(responsavel, df_import):
    conn = get_conn()

    for _, row in df_import.iterrows():
        conn.execute(
            """
            INSERT INTO despesas(
                responsavel,
                data,
                fornecedor,
                objeto,
                valor,
                categoria
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                responsavel,
                str(row["Data"]),
                str(row["Fornecedor"]),
                str(row["Objeto"]),
                float(row["Valor"]),
                str(row["Categoria"])
            )
        )

    conn.commit()
    conn.close()

    clear_cache()


@st.cache_data
def gerar_grafico(df_json):
    df = pd.read_json(df_json)

    if df.empty:
        return None

    por_cat = df.groupby("Categoria")["Valor"].sum()

    fig, ax = plt.subplots(figsize=(5, 3))

    ax.pie(
        por_cat.values,
        labels=por_cat.index,
        autopct='%1.1f%%'
    )

    buf = BytesIO()

    plt.savefig(buf, format="png", bbox_inches='tight')

    plt.close(fig)

    return base64.b64encode(buf.getvalue()).decode()



def gerar_pdf(html):
    return HTML(string=html).write_pdf()


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.title("💼 ERP Financeiro")

    clientes = get_clientes()

    responsavel = st.selectbox(
        "Responsável",
        list(clientes.keys())
    )

    st.divider()

    st.subheader("Novo Cliente")

    with st.form("novo_cliente"):

        nome = st.text_input("Nome")
        documento = st.text_input("CPF/CNPJ")

        salvar_cliente = st.form_submit_button("Cadastrar")

        if salvar_cliente:

            if nome and documento:

                ok = add_cliente(nome, documento)

                if ok:
                    st.success("Cliente cadastrado")
                    st.rerun()
                else:
                    st.error("Cliente já existe")

# ==========================================
# LOAD DATA
# ==========================================

if "df_master" not in st.session_state:
    st.session_state.df_master = pd.DataFrame()

st.session_state.df_master = get_despesas(responsavel)


df = st.session_state.df_master

# ==========================================
# HEADER
# ==========================================

st.title(f"💼 Caixa de Obra — {responsavel}")
st.caption(clientes[responsavel])

# ==========================================
# TABS
# ==========================================

aba1, aba2, aba3 = st.tabs([
    "📋 Lançamentos",
    "📊 Dashboard",
    "📄 PDF"
])

# ==========================================
# ABA 1
# ==========================================

with aba1:

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Nova Despesa")

        with st.form("nova_despesa"):

            data = st.date_input("Data", value=date.today())
            fornecedor = st.text_input("Fornecedor")
            objeto = st.text_input("Objeto")

            c1, c2 = st.columns(2)

            with c1:
                valor = st.number_input(
                    "Valor",
                    min_value=0.0,
                    step=1.0
                )

            with c2:
                categoria = st.selectbox(
                    "Categoria",
                    CATEGORIAS
                )

            salvar = st.form_submit_button(
                "Adicionar",
                use_container_width=True
            )

            if salvar:

                if fornecedor and objeto and valor > 0:

                    add_despesa(
                        responsavel,
                        data,
                        fornecedor,
                        objeto,
                        valor,
                        categoria
                    )

                    st.success("Despesa adicionada")
                    st.rerun()

    with col2:

        st.subheader("Importação em Massa")

        raw = st.text_area(
            "Cole os dados do Excel",
            height=180
        )

        if st.button("Importar"):

            if raw.strip():

                try:

                    df_imp = pd.read_csv(
                        io.StringIO(raw),
                        sep="\t",
                        names=[
                            "Data",
                            "Fornecedor",
                            "Objeto",
                            "Valor",
                            "Categoria"
                        ]
                    )

                    df_imp["Valor"] = pd.to_numeric(
                        df_imp["Valor"]
                        .astype(str)
                        .str.replace("R$", "")
                        .str.replace(".", "", regex=False)
                        .str.replace(",", ".", regex=False),
                        errors="coerce"
                    ).fillna(0)

                    import_bulk(responsavel, df_imp)

                    st.success(f"{len(df_imp)} registros importados")

                    st.rerun()

                except Exception as e:
                    st.error(str(e))

    st.divider()

    st.subheader("Despesas")

    if df.empty:

        st.info("Nenhuma despesa")

    else:

        df_view = df.copy()

        df_view["Valor"] = df_view["Valor"].apply(
            lambda x: f"R$ {formatar_br(x)}"
        )

        st.dataframe(
            df_view,
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# ABA 2
# ==========================================

with aba2:

    adiantamento = st.number_input(
        "Adiantamento",
        min_value=0.0,
        step=100.0
    )

    total = float(df["Valor"].sum()) if not df.empty else 0

    saldo = total - adiantamento

    c1, c2, c3 = st.columns(3)

    c1.metric("Total", f"R$ {formatar_br(total)}")
    c2.metric("Adiantamento", f"R$ {formatar_br(adiantamento)}")
    c3.metric("Saldo", f"R$ {formatar_br(abs(saldo))}")

    if not df.empty:

        st.divider()

        col_g1, col_g2 = st.columns(2)

        with col_g1:

            por_cat = df.groupby("Categoria")["Valor"].sum().reset_index()

            fig = px.pie(
                por_cat,
                values="Valor",
                names="Categoria",
                hole=0.4
            )

            st.plotly_chart(fig, use_container_width=True)

        with col_g2:

            top = df.groupby("Fornecedor")["Valor"] \
                .sum() \
                .nlargest(10) \
                .reset_index()

            fig2 = px.bar(
                top,
                x="Valor",
                y="Fornecedor",
                orientation="h"
            )

            st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# ABA 3
# ==========================================

with aba3:

    st.subheader("Relatório PDF")

    arquivos = st.file_uploader(
        "Anexar comprovantes",
        accept_multiple_files=True,
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if st.button("Gerar PDF"):

        total = float(df["Valor"].sum()) if not df.empty else 0

        linhas = ""

        for _, row in df.iterrows():

            linhas += f"""
            <tr>
                <td>{row['Data']}</td>
                <td>{row['Fornecedor']}</td>
                <td>{row['Objeto']}</td>
                <td>{row['Categoria']}</td>
                <td>R$ {formatar_br(row['Valor'])}</td>
            </tr>
            """

        html = f"""
        <html>
        <body>

        <h1>Prestação de Contas</h1>

        <p><b>Responsável:</b> {responsavel}</p>
        <p><b>Total:</b> R$ {formatar_br(total)}</p>

        <table border="1" cellspacing="0" cellpadding="5" width="100%">
            <tr>
                <th>Data</th>
                <th>Fornecedor</th>
                <th>Objeto</th>
                <th>Categoria</th>
                <th>Valor</th>
            </tr>
            {linhas}
        </table>

        </body>
        </html>
        """

        pdf_bytes = gerar_pdf(html)

        st.success("PDF gerado")

        st.download_button(
            "Baixar PDF",
            data=pdf_bytes,
            file_name="relatorio.pdf",
            mime="application/pdf"
        )

```
