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
    import fitz  # PyMuPDF — Otimizado para manipular e comprimir PDFs
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


def delete_despesas(ids: list):
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany("DELETE FROM despesas WHERE id=?", [(i,) for i in ids])


def import_bulk(responsavel: str, df_import: pd.DataFrame):
    with sqlite3.connect(DB_PATH) as conn:
        for _, row in df_import.iterrows():
            conn.execute(
                "INSERT INTO despesas (responsavel,data,fornecedor,objeto,valor,categoria) VALUES (?,?,?,?,?,?)",
                (responsavel, str(row["Data"]), str(row["Fornecedor"]),
                 str(row["Objeto"]), float(row["Valor"]), str(row.get("Categoria", "Outros")))
            )


def purgar_responsavel(responsavel: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM despesas WHERE responsavel=?", (responsavel,))

# ==========================================
# 3. UTILITÁRIOS
# ==========================================

def formatar_br(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def logo_b64(path="logo.png") -> str | None:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def gerar_grafico_pizza(df: pd.DataFrame) -> str | None:
    """Donut com legenda lateral — sem labels sobrepostos no PDF."""
    if df.empty or "Categoria" not in df.columns:
        return None
    por_cat = df.groupby("Categoria")["Valor"].sum().sort_values(ascending=False)
    if por_cat.empty:
        return None

    cores = ["#0f172a", "#1e40af", "#0369a1", "#0891b2",
             "#059669", "#d97706", "#7c3aed"]
    total = por_cat.sum()

    fig, ax = plt.subplots(figsize=(6.2, 3.2), facecolor="#ffffff")
    fig.patch.set_facecolor("#ffffff")

    wedges, _, autotexts = ax.pie(
        por_cat.values,
        autopct="%1.1f%%",
        colors=cores[:len(por_cat)],
        startangle=90,
        pctdistance=0.75,
        wedgeprops={"linewidth": 1.5, "edgecolor": "#ffffff"},
        textprops={"fontsize": 8.5, "fontfamily": "DejaVu Sans"}
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
        at.set_fontsize(8)

    centro = plt.Circle((0, 0), 0.52, color="#ffffff")
    ax.add_patch(centro)
    ax.text(0, 0.10, "Total", ha="center", va="center",
            fontsize=7, color="#64748b", fontfamily="DejaVu Sans")
    valor_fmt = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    ax.text(0, -0.15, valor_fmt, ha="center", va="center",
            fontsize=8, fontweight="bold", color="#0f172a",
            fontfamily="DejaVu Sans")

    legend_labels = []
    for cat, val in por_cat.items():
        val_fmt = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        legend_labels.append(f"  {cat}   {val_fmt}  ({val/total*100:.1f}%)")

    ax.legend(
        wedges, legend_labels,
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        fontsize=7.5,
        frameon=False,
        labelspacing=1.0,
        handlelength=1.2,
        handleheight=1.0,
    )
    ax.set_facecolor("#ffffff")
    plt.tight_layout(pad=0.3)

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=160,
                bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def gerar_pdf(html_content: str) -> bytes | None:
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    return result.getvalue() if not pdf.err else None


# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<p class='header-title'>M e Lopes</p>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>ERP Financeiro v11.0</p>", unsafe_allow_html=True)
    st.divider()

    clientes = get_clientes()
    responsavel = st.selectbox("👤 Responsável Ativo", list(clientes.keys()))

    st.divider()
    st.markdown("##### ➕ Novo Cliente / Responsável")
    with st.form("form_cliente", clear_on_submit=True):
        novo_nome = st.text_input("Nome ou Empresa")
        novo_doc  = st.text_input("CPF ou CNPJ")
        if st.form_submit_button("Cadastrar", use_container_width=True):
            if novo_nome and novo_doc:
                ok = add_cliente(novo_nome, novo_doc)
                st.success("Cadastrado com sucesso!") if ok else st.error("Já existe.")
                if ok:
                    st.rerun()
            else:
                st.warning("Preencha nome e documento.")

    st.divider()
    if st.button("🗑️ Purgar Despesas do Responsável",
                 use_container_width=True, type="secondary"):
        purgar_responsavel(responsavel)
        st.rerun()

# ==========================================
# 5. CABEÇALHO DA PÁGINA
# ==========================================
st.markdown(f"## 💼 Caixa de Obra — {responsavel}")
st.caption(f"Documento: {clientes[responsavel]}")
st.divider()

tab_lancamentos, tab_dashboard, tab_relatorio = st.tabs(
    ["📋 Lançamentos", "📊 Dashboard", "📄 Relatório PDF"]
)

# ==========================================
# ABA 1 — LANÇAMENTOS
# ==========================================
with tab_lancamentos:

    col_form, col_import = st.columns([1, 1], gap="large")

    # ---- Formulário Manual ----
    with col_form:
        st.markdown("#### Lançamento Manual")
        with st.form("form_lancamento", clear_on_submit=True):
            data_desp  = st.date_input("Data", value=date.today())
            fornecedor = st.text_input("Fornecedor / Estabelecimento")
            objeto     = st.text_input("Objeto / Descrição")
            c1, c2 = st.columns(2)
            with c1:
                valor     = st.number_input("Valor (R$)", min_value=0.01, step=1.0, format="%.2f")
            with c2:
                categoria = st.selectbox("Categoria", CATEGORIAS)

            ok = st.form_submit_button("✅ Adicionar Despesa",
                                       use_container_width=True, type="primary")
            if ok:
                if fornecedor.strip() and objeto.strip() and valor > 0:
                    add_despesa(responsavel, data_desp, fornecedor.strip(),
                                objeto.strip(), valor, categoria)
                    st.success("Despesa adicionada!")
                    st.rerun()
                else:
                    st.error("Preencha todos os campos corretamente.")

    # ---- Importação em Lote ----
    with col_import:
        st.markdown("#### Importação em Lote (Excel → Cole aqui)")
        st.caption("Colunas esperadas: **Data \\t Fornecedor \\t Objeto \\t Valor \\t Categoria**")
        raw = st.text_area(
            "Cole os dados:",
            height=160,
            placeholder="01/01/2025\tFornecedor X\tMaterial Y\t150,00\tMaterial"
        )
        if st.button("📥 Importar Dados", use_container_width=True):
            if raw.strip():
                try:
                    df_imp = pd.read_csv(io.StringIO(raw), sep="\t",
                                         names=["Data", "Fornecedor", "Objeto", "Valor", "Categoria"])
                    df_imp["Valor"] = df_imp["Valor"].apply(
                        lambda x: float(str(x).replace("R$","").replace(".","").replace(",",".").strip())
                    )
                    import_bulk(responsavel, df_imp)
                    st.success(f"{len(df_imp)} registro(s) importado(s)!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro na importação: {e}")
            else:
                st.warning("Cole os dados antes de importar.")

    # ---- Grade de Despesas ----
    st.divider()
    st.markdown("#### Despesas Lançadas")
    df = get_despesas(responsavel)

    if df.empty:
        st.info("Nenhuma despesa lançada ainda. Use o formulário ou a importação acima.")
    else:
        df_view = df.copy()
        df_view["Valor_fmt"] = df_view["Valor"].apply(lambda x: f"R$ {formatar_br(x)}")
        st.dataframe(
            df_view[["Data", "Fornecedor", "Objeto", "Categoria", "Valor_fmt"]]
              .rename(columns={"Valor_fmt": "Valor"}),
            use_container_width=True,
            hide_index=True
        )

        with st.expander("🗑️ Excluir registros individuais"):
            ids   = df["id"].tolist()
            rotulos = [
                f"#{r['id']} | {r['Data']} | {r['Fornecedor']} | R$ {formatar_br(r['Valor'])}"
                for _, r in df.iterrows()
            ]
            sel = st.multiselect("Selecione para excluir:", ids,
                                 format_func=lambda x: rotulos[ids.index(x)])
            if st.button("Excluir Selecionados", type="primary") and sel:
                delete_despesas(sel)
                st.rerun()

# ==========================================
# ABA 2 — DASHBOARD
# ==========================================
with tab_dashboard:
    df = get_despesas(responsavel)

    val_adiantamento = st.number_input(
        "💰 Adiantamento Recebido (R$)", min_value=0.0, step=100.0, key="adiant_dash"
    )

    val_gasto = float(df["Valor"].sum()) if not df.empty else 0.0
    val_saldo = val_gasto - val_adiantamento
    lbl_saldo = "🔴 A Reembolsar" if val_saldo > 0 else "🟢 Devolução ao Resp."

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros",         len(df))
    c2.metric("Gasto Total",       f"R$ {formatar_br(val_gasto)}")
    c3.metric("Adiantamento",      f"R$ {formatar_br(val_adiantamento)}")
    c4.metric(lbl_saldo,           f"R$ {formatar_br(abs(val_saldo))}")

    if not df.empty:
        st.divider()
        cg1, cg2 = st.columns(2)

        with cg1:
            st.markdown("##### Gasto por Categoria")
            por_cat = df.groupby("Categoria")["Valor"].sum().reset_index()
            fig_pizza = px.pie(
                por_cat, values="Valor", names="Categoria",
                color_discrete_sequence=px.colors.sequential.Blues_r,
                hole=0.42
            )
            fig_pizza.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=290,
                                    legend=dict(font_size=11))
            st.plotly_chart(fig_pizza, use_container_width=True)

        with cg2:
            st.markdown("##### Top Fornecedores")
            top_forn = df.groupby("Fornecedor")["Valor"].sum().nlargest(8).reset_index()
            fig_bar = px.bar(
                top_forn, x="Valor", y="Fornecedor", orientation="h",
                color="Valor", color_continuous_scale="Blues", text_auto=".2s"
            )
            fig_bar.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), height=290,
                coloraxis_showscale=False,
                yaxis={"categoryorder": "total ascending"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("##### Evolução Acumulada dos Gastos")
        df_t = df.copy()
        df_t["Data"] = pd.to_datetime(df_t["Data"], errors="coerce", dayfirst=True)
        df_t = df_t.dropna(subset=["Data"])
        if not df_t.empty:
            df_agg = df_t.groupby(df_t["Data"].dt.date)["Valor"].sum().reset_index()
            df_agg["Acumulado"] = df_agg["Valor"].cumsum()
            fig_area = px.area(
                df_agg, x="Data", y="Acumulado",
                color_discrete_sequence=["#0f172a"],
                labels={"Acumulado": "Gasto Acumulado (R$)", "Data": ""}
            )
            fig_area.update_layout(margin=dict(t=10, b=10), height=230)
            st.plotly_chart(fig_area, use_container_width=True)

# ==========================================
# ABA 3 — RELATÓRIO PDF (OTIMIZADO)
# ==========================================
with tab_relatorio:
    df = get_despesas(responsavel)

    val_adiantamento_pdf = st.number_input(
        "💰 Adiantamento para o Relatório (R$)", min_value=0.0, step=100.0, key="adiant_pdf"
    )

    up_files = st.file_uploader(
        "📎 Anexar Comprovantes e Notas Fiscais (PDFs e Imagens)",
        accept_multiple_files=True,
        type=["pdf", "png", "jpg", "jpeg", "webp"]
    )

    if up_files:
        if any(f.type == "application/pdf" for f in up_files) and not PYMUPDF_OK:
            st.warning(
                "⚠️ Comprovantes PDF detectados, mas **PyMuPDF** não está instalado. "
                "Execute `pip install pymupdf` para conseguir acoplá-los ao relatório."
            )
        st.success(f"✅ {len(up_files)} arquivo(s) carregado(s). Eles serão otimizados e anexados ao final do documento.")

        # Visualizador de auditoria na tela
        sel_file = st.selectbox("Auditar comprovante na tela:", [f.name for f in up_files])
        for f in up_files:
            if f.name == sel_file:
                if f.type == "application/pdf":
                    b64_view = base64.b64encode(f.getvalue()).decode()
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64_view}" '
                        f'width="100%" height="420" type="application/pdf"></iframe>',
                        unsafe_allow_html=True
                    )
                else:
                    st.image(f, use_container_width=True)

    st.divider()

    if df.empty:
        st.info("Lance despesas na aba **Lançamentos** para gerar o relatório.")
        st.stop()

    # ---- Monta HTML da Capa Financeira ----
    val_gasto_pdf = float(df["Valor"].sum())
    val_saldo_pdf = val_gasto_pdf - val_adiantamento_pdf
    label_saldo   = "A Reembolsar" if val_saldo_pdf > 0 else "Devolução ao Responsável"
    cor_saldo     = "#dc2626"      if val_saldo_pdf > 0 else "#059669"

    lb64   = logo_b64()
    logo_h = (f'<img src="data:image/png;base64,{lb64}" height="38" style="display:block;">'
              if lb64 else "")

    pizza_b64  = gerar_grafico_pizza(df)
    pizza_html = (f'<img src="data:image/png;base64,{pizza_b64}" width="340" style="display:block;margin:0 auto;">'
                  if pizza_b64 else "<p style='color:#64748b;font-size:9px;text-align:center;'>—</p>")

    # Tabela de resumo por categoria
    por_cat = df.groupby("Categoria")["Valor"].agg(["sum","count"]).reset_index()
    por_cat.columns = ["Categoria", "Total", "Qtd"]
    linhas_cat = ""
    for _, r in por_cat.iterrows():
        pct = (r["Total"] / val_gasto_pdf * 100) if val_gasto_pdf else 0
        linhas_cat += f"""<tr>
            <td>{r["Categoria"]}</td>
            <td style="text-align:center">{int(r["Qtd"])}</td>
            <td style="text-align:right">R$ {formatar_br(r["Total"])}</td>
            <td style="text-align:right">{pct:.1f}%</td>
        </tr>"""

    # Linhas de detalhe
    linhas_det = ""
    for i, row in df.iterrows():
        linhas_det += f"""<tr>
            <td>{row["Data"]}</td>
            <td>{row["Fornecedor"]}</td>
            <td>{row["Objeto"]}</td>
            <td>{row["Categoria"]}</td>
            <td class="r">R$ {formatar_br(float(row["Valor"]))}</td>
        </tr>"""

    linhas_det += f"""<tr class="t-total">
        <td colspan="4">TOTAL DAS DESPESAS</td>
        <td>R$ {formatar_br(val_gasto_pdf)}</td>
    </tr>"""

    now_str  = datetime.now().strftime("%d/%m/%Y &agrave;s %H:%M")
    ref_str  = datetime.now().strftime("%m/%Y")

    html_pdf = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: a4 portrait;
        margin: 0 0 1.8cm 0;
        @frame body_frame {{
            left: 1.7cm; width: 17.6cm;
            top: 3.2cm; height: 23.5cm;
        }}
        @frame footer_frame {{
            -pdf-frame-content: footer_content;
            left: 1.7cm; width: 17.6cm;
            top: 27.2cm; height: 0.8cm;
        }}
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        color: #1e293b;
        font-size: 9.5px;
        margin: 0; padding: 0;
    }}

    /* ── CABEÇALHO ESCURO ── */
    .hdr-bar {{
        background: #0f172a;
        padding: 14px 20px 12px 20px;
        margin-bottom: 14px;
    }}
    .hdr-empresa {{
        font-size: 15px; font-weight: bold;
        color: #ffffff; margin: 0 0 1px 0;
    }}
    .hdr-sub {{
        font-size: 8px; color: #94a3b8; margin: 0;
    }}
    .hdr-titulo {{
        font-size: 13px; font-weight: bold;
        color: #ffffff; text-align: right; margin: 0 0 2px 0;
    }}
    .hdr-emissao {{
        font-size: 8px; color: #94a3b8;
        text-align: right; margin: 0;
    }}

    /* ── KPI CARDS ── */
    .kpi-wrap {{
        margin-bottom: 14px;
    }}
    .kpi-card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-top: 3px solid #0f172a;
        padding: 8px 10px;
        vertical-align: top;
    }}
    .kpi-label {{
        font-size: 7.5px; color: #64748b;
        text-transform: uppercase; letter-spacing: .5px;
        margin-bottom: 4px;
    }}
    .kpi-value {{
        font-size: 11px; font-weight: bold; color: #0f172a;
    }}

    /* ── TÍTULOS DE SEÇÃO ── */
    .sec {{
        font-size: 9px; font-weight: bold; color: #0f172a;
        text-transform: uppercase; letter-spacing: .6px;
        background: #e2e8f0;
        padding: 5px 8px;
        margin: 14px 0 6px 0;
    }}

    /* ── TABELA RESUMO ── */
    .t-resumo {{ width: 100%; border-collapse: collapse; }}
    .t-resumo th {{
        background: #1e40af; color: #fff;
        padding: 5px 8px; font-size: 8.5px;
        text-transform: uppercase; text-align: left;
    }}
    .t-resumo td {{
        border-bottom: 1px solid #f1f5f9;
        padding: 4px 8px; font-size: 9px;
    }}
    .t-resumo tr:nth-child(even) td {{ background: #f8fafc; }}

    /* ── TABELA DETALHE ── */
    .t-det {{ width: 100%; border-collapse: collapse; }}
    .t-det th {{
        background: #0f172a; color: #fff;
        padding: 5px 7px; font-size: 8px;
        text-transform: uppercase; text-align: left;
    }}
    .t-det th.r {{ text-align: right; }}
    .t-det td {{
        border-bottom: 1px solid #f1f5f9;
        padding: 4px 7px; font-size: 8.5px;
    }}
    .t-det td.r {{ text-align: right; font-weight: 600; }}
    .t-det tr:nth-child(even) td {{ background: #f8fafc; }}
    .t-total td {{
        background: #0f172a !important;
        color: #fff; font-weight: bold;
        font-size: 9.5px; padding: 6px 7px;
        text-align: right;
        border-top: 2px solid #0f172a;
    }}
    .t-total td:first-child {{ text-align: left; }}

    /* ── RODAPÉ SALDO ── */
    .saldo-bloco {{
        border-left: 4px solid {cor_saldo};
        background: #f8fafc;
        padding: 10px 14px;
        margin-top: 12px;
    }}
    .saldo-lbl {{ font-size: 7.5px; color: #64748b; text-transform: uppercase; }}
    .saldo-val {{ font-size: 15px; font-weight: bold; color: {cor_saldo}; }}
    .saldo-adiant {{
        font-size: 10px; font-weight: 600;
        color: #0f172a; margin: 2px 0 8px 0;
    }}

    /* ── ASSINATURA ── */
    .ass-linha {{
        border-top: 1px solid #334155;
        padding-top: 5px;
        text-align: center;
        font-size: 8.5px; color: #64748b;
        width: 200px;
    }}

    /* ── FOOTER ── */
    #footer_content {{
        text-align: center; font-size: 7.5px; color: #94a3b8;
        border-top: 1px solid #e2e8f0; padding-top: 5px;
    }}
</style>
</head>
<body>

<div id="footer_content">
    M e Lopes Assessoria em Tecnologia &nbsp;&bull;&nbsp;
    {now_str} &nbsp;&bull;&nbsp; Documento n&atilde;o fiscal
</div>

<table class="hdr-bar" width="100%">
    <tr>
        <td style="vertical-align:middle; width:50%;">
            {logo_h}
            <p class="hdr-empresa" style="{'display:none' if lb64 else ''}">M e Lopes</p>
            <p class="hdr-sub">Assessoria em Tecnologia</p>
        </td>
        <td style="vertical-align:middle; width:50%;">
            <p class="hdr-titulo">Presta&ccedil;&atilde;o de Contas &mdash; Caixa de Obra</p>
            <p class="hdr-emissao">Emiss&atilde;o: {now_str} &nbsp;|&nbsp; Ref: {ref_str}</p>
        </td>
    </tr>
</table>

<table class="kpi-wrap" width="100%" style="border-collapse:separate; border-spacing:6px 0;">
    <tr>
        <td class="kpi-card" width="25%">
            <div class="kpi-label">Respons&aacute;vel</div>
            <div class="kpi-value" style="font-size:10px;">{responsavel}</div>
        </td>
        <td class="kpi-card" width="25%">
            <div class="kpi-label">Documento</div>
            <div class="kpi-value" style="font-size:10px;">{clientes[responsavel]}</div>
        </td>
        <td class="kpi-card" width="25%">
            <div class="kpi-label">Registros</div>
            <div class="kpi-value">{len(df)}</div>
        </td>
        <td class="kpi-card" width="25%">
            <div class="kpi-label">Gasto Total</div>
            <div class="kpi-value">R$ {formatar_br(val_gasto_pdf)}</div>
        </td>
    </tr>
</table>

<div class="sec">Resumo por Categoria</div>
<table width="100%">
    <tr>
        <td width="42%" style="vertical-align:top; padding-right:10px;">
            <table class="t-resumo">
                <thead>
                    <tr>
                        <th>Categoria</th>
                        <th style="text-align:center; width:40px;">Qtd.</th>
                        <th style="text-align:right;">Total</th>
                        <th style="text-align:right; width:36px;">%</th>
                    </tr>
                </thead>
                <tbody>{linhas_cat}</tbody>
            </table>
        </td>
        <td width="58%" style="vertical-align:middle; text-align:center;">
            {pizza_html}
        </td>
    </tr>
</table>

<div class="sec">Detalhamento das Despesas</div>
<table class="t-det">
    <thead>
        <tr>
            <th style="width:11%">Data</th>
            <th style="width:30%">Fornecedor</th>
            <th style="width:26%">Objeto</th>
            <th style="width:14%">Categoria</th>
            <th class="r" style="width:13%">Valor</th>
        </tr>
    </thead>
    <tbody>{linhas_det}</tbody>
</table>

<table width="100%" style="margin-top:12px;">
    <tr>
        <td width="55%" style="vertical-align:top;">
            <div class="saldo-bloco">
                <div class="saldo-lbl">Adiantamento Recebido</div>
                <div class="saldo-adiant">R$ {formatar_br(val_adiantamento_pdf)}</div>
                <div class="saldo-lbl">{label_saldo}</div>
                <div class="saldo-val">R$ {formatar_br(abs(val_saldo_pdf))}</div>
            </div>
        </td>
        <td width="45%" style="text-align:center; vertical-align:bottom; padding-bottom:2px;">
            <div style="margin-top:44px;">
                <div class="ass-linha">
                    {responsavel}<br/>Respons&aacute;vel pelo Caixa
                </div>
            </div>
        </td>
    </tr>
</table>
</body>
</html>"""

    # Passo 1: Gera a "Capa Financeira" super leve
    pdf_bytes = gerar_pdf(html_pdf)

    # Passo 2: Mescla os Anexos Pesados (PDFs/Imagens) diretamente usando o PyMuPDF
    if pdf_bytes:
        qtd_anexos = 0
        if up_files and PYMUPDF_OK:
            try:
                # Transforma a capa base em um documento editável do PyMuPDF
                doc_final = fitz.open("pdf", pdf_bytes)
                
                for up_file in up_files:
                    file_bytes = up_file.getvalue()
                    
                    if up_file.type == "application/pdf":
                        # Abre o PDF anexo e grampeia inteiro no final instantaneamente
                        doc_anexo = fitz.open("pdf", file_bytes)
                        doc_final.insert_pdf(doc_anexo)
                        doc_anexo.close()
                    else:
                        # Se for imagem, comprime a qualidade para não pesar o arquivo final
                        img = Image.open(BytesIO(file_bytes)).convert("RGB")
                        img.thumbnail((1200, 1600)) # Compressão de dimensão
                        img_byte_arr = BytesIO()
                        img.save(img_byte_arr, format='JPEG', quality=75) # Compressão de qualidade
                        
                        # Transforma a imagem leve em PDF e grampeia
                        img_doc = fitz.open("pdf", fitz.open("jpeg", img_byte_arr.getvalue()).convert_to_pdf())
                        doc_final.insert_pdf(img_doc)
                        img_doc.close()
                        
                    qtd_anexos += 1
                
                # Passo 3: Salva o arquivo final aplicando COMPRESSÃO MÁXIMA
                pdf_bytes = doc_final.write(garbage=4, deflate=True)
                doc_final.close()
                
            except Exception as e:
                st.error(f"Erro ao anexar comprovantes nativos: {e}")

        # Finalização e Download
        msg = "✅ Relatório gerado com sucesso!"
        if qtd_anexos > 0:
            msg += f" ({qtd_anexos} lote(s) de comprovantes foram comprimidos e anexados.)"
        st.success(msg)
        
        st.download_button(
            "📥 Baixar Relatório Completo (PDF)",
            data=pdf_bytes,
            file_name=f"Relatorio_Caixa_{responsavel.replace(' ', '_')}_{datetime.now().strftime('%Y%m')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    else:
        st.error("Falha ao gerar o PDF. Verifique se as bibliotecas necessárias estão instaladas.")
