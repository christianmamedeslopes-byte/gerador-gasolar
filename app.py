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
    """Gráfico de pizza Matplotlib → base64 para embutir no PDF."""
    if df.empty or "Categoria" not in df.columns:
        return None
    por_cat = df.groupby("Categoria")["Valor"].sum()
    if por_cat.empty:
        return None

    cores = ["#0f172a", "#1e3a5f", "#1e40af", "#0369a1",
             "#0891b2", "#059669", "#d97706"]

    fig, ax = plt.subplots(figsize=(4.5, 3.2), facecolor="#f8fafc")
    wedges, texts, autotexts = ax.pie(
        por_cat.values,
        labels=por_cat.index,
        autopct="%1.1f%%",
        colors=cores[:len(por_cat)],
        startangle=140,
        pctdistance=0.78,
        textprops={"fontsize": 8, "fontfamily": "DejaVu Sans"}
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_facecolor("#f8fafc")
    plt.tight_layout(pad=0.5)

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#f8fafc")
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
# ABA 3 — RELATÓRIO PDF
# ==========================================
with tab_relatorio:
    df = get_despesas(responsavel)

    val_adiantamento_pdf = st.number_input(
        "💰 Adiantamento para o Relatório (R$)", min_value=0.0, step=100.0, key="adiant_pdf"
    )

    up_files = st.file_uploader(
        "📎 Anexar Comprovantes para Conferência", accept_multiple_files=True
    )
    if up_files:
        st.success(f"✅ {len(up_files)} arquivo(s) em memória.")
        sel_file = st.selectbox("Auditar comprovante:", [f.name for f in up_files])
        for f in up_files:
            if f.name == sel_file:
                if f.type == "application/pdf":
                    b64 = base64.b64encode(f.getvalue()).decode()
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64}" '
                        f'width="100%" height="420" type="application/pdf"></iframe>',
                        unsafe_allow_html=True
                    )
                else:
                    st.image(f, use_column_width=True)

    st.divider()

    if df.empty:
        st.info("Lance despesas na aba **Lançamentos** para gerar o relatório.")
        st.stop()

    # ---- Monta HTML do PDF ----
    val_gasto_pdf = float(df["Valor"].sum())
    val_saldo_pdf = val_gasto_pdf - val_adiantamento_pdf
    label_saldo   = "A Reembolsar" if val_saldo_pdf > 0 else "Devolução ao Responsável"
    cor_saldo     = "#dc2626"      if val_saldo_pdf > 0 else "#059669"

    lb64   = logo_b64()
    logo_h = (f'<img src="data:image/png;base64,{lb64}" height="42">'
              if lb64 else '<strong style="font-size:18px;color:#0f172a;">M e Lopes</strong>')

    pizza_b64  = gerar_grafico_pizza(df)
    pizza_html = (f'<img src="data:image/png;base64,{pizza_b64}" width="300">'
                  if pizza_b64 else "<p style='color:#64748b;font-size:9px;'>—</p>")

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
        cls = 'class="zebra"' if i % 2 == 0 else ""
        linhas_det += f"""<tr {cls}>
            <td>{row["Data"]}</td>
            <td>{row["Fornecedor"]}</td>
            <td>{row["Objeto"]}</td>
            <td>{row["Categoria"]}</td>
            <td class="right">R$ {formatar_br(float(row["Valor"]))}</td>
        </tr>"""

    linhas_det += f"""<tr class="total-row">
        <td colspan="4">TOTAL DAS DESPESAS:</td>
        <td class="right">R$ {formatar_br(val_gasto_pdf)}</td>
    </tr>"""

    now_str = datetime.now().strftime("%d/%m/%Y &agrave;s %H:%M")

    html_pdf = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: a4 portrait;
        margin: 1.8cm 1.8cm 2.8cm 1.8cm;
        @frame footer_frame {{
            -pdf-frame-content: footer_content;
            left: 50pt; width: 512pt; top: 800pt; height: 25pt;
        }}
    }}
    body {{ font-family: Helvetica, Arial, sans-serif; color: #334155; font-size: 10px; }}

    /* HEADER */
    .header {{ width:100%; border-bottom: 3px solid #0f172a; padding-bottom: 12px; margin-bottom: 16px; }}
    .doc-title {{ font-size:17px; font-weight:bold; color:#0f172a; margin:0 0 2px 0; }}
    .doc-sub   {{ font-size:9px;  color:#64748b; margin:0; }}

    /* KPI */
    .kpi-box   {{ background:#f1f5f9; border-left:4px solid #0f172a; padding:10px 14px; margin-bottom:16px; }}
    .kpi-label {{ font-size:8px; color:#64748b; text-transform:uppercase; letter-spacing:.5px; margin-bottom:2px; }}
    .kpi-value {{ font-size:13px; font-weight:bold; color:#0f172a; }}

    /* SECTION */
    .sec-title {{ font-size:10px; font-weight:bold; color:#0f172a; text-transform:uppercase;
                  letter-spacing:.5px; border-bottom:1px solid #e2e8f0;
                  padding-bottom:4px; margin:16px 0 8px 0; }}

    /* SUMMARY TABLE */
    .sum-table {{ width:100%; border-collapse:collapse; }}
    .sum-table th {{ background:#1e40af; color:#fff; padding:6px 8px;
                     font-size:9px; text-transform:uppercase; text-align:left; }}
    .sum-table td {{ border-bottom:1px solid #e2e8f0; padding:5px 8px; font-size:10px; }}

    /* DETAIL TABLE */
    .det-table {{ width:100%; border-collapse:collapse; }}
    .det-table th {{ background:#0f172a; color:#fff; padding:7px 8px;
                     font-size:9px; text-transform:uppercase; text-align:left; }}
    .det-table th.right {{ text-align:right; }}
    .det-table td {{ border-bottom:1px solid #e2e8f0; padding:6px 8px; font-size:10px; }}
    .det-table td.right {{ text-align:right; font-weight:600; }}
    .zebra td   {{ background:#f8fafc; }}
    .total-row td {{ background:#e2e8f0; font-weight:bold; color:#0f172a;
                     text-align:right; border-top:2px solid #0f172a;
                     font-size:11px; padding:8px; }}

    /* SALDO */
    .saldo-box   {{ border:2px solid {cor_saldo}; padding:10px 14px; margin-top:14px; }}
    .saldo-label {{ font-size:8px; color:#64748b; text-transform:uppercase; margin-bottom:4px; }}
    .saldo-value {{ font-size:16px; font-weight:bold; color:{cor_saldo}; }}

    /* FOOTER */
    #footer_content {{ text-align:center; font-size:8px; color:#94a3b8;
                        border-top:1px solid #e2e8f0; padding-top:7px; }}
</style>
</head>
<body>

<div id="footer_content">
    M e Lopes Assessoria em Tecnologia &nbsp;|&nbsp; {now_str} &nbsp;|&nbsp; Documento n&atilde;o fiscal
</div>

<!-- CABEÇALHO -->
<table class="header">
    <tr>
        <td style="width:50%;vertical-align:middle;">{logo_h}</td>
        <td style="width:50%;vertical-align:middle;text-align:right;">
            <p class="doc-title">Presta&ccedil;&atilde;o de Contas &mdash; Caixa de Obra</p>
            <p class="doc-sub">Emiss&atilde;o: {now_str} &nbsp;|&nbsp; Ref: {datetime.now().strftime("%m/%Y")}</p>
        </td>
    </tr>
</table>

<!-- KPIs -->
<div class="kpi-box">
    <table width="100%">
        <tr>
            <td width="25%">
                <div class="kpi-label">Respons&aacute;vel</div>
                <div class="kpi-value">{responsavel}</div>
            </td>
            <td width="25%">
                <div class="kpi-label">Documento</div>
                <div class="kpi-value">{clientes[responsavel]}</div>
            </td>
            <td width="25%">
                <div class="kpi-label">Total de Registros</div>
                <div class="kpi-value">{len(df)}</div>
            </td>
            <td width="25%">
                <div class="kpi-label">Gasto Total</div>
                <div class="kpi-value">R$ {formatar_br(val_gasto_pdf)}</div>
            </td>
        </tr>
    </table>
</div>

<!-- RESUMO + GRÁFICO -->
<p class="sec-title">Resumo por Categoria</p>
<table width="100%">
    <tr>
        <td width="55%" style="vertical-align:top; padding-right:14px;">
            <table class="sum-table">
                <thead>
                    <tr>
                        <th>Categoria</th>
                        <th style="text-align:center">Qtd.</th>
                        <th style="text-align:right">Total</th>
                        <th style="text-align:right">%</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_cat}
                </tbody>
            </table>
        </td>
        <td width="45%" style="vertical-align:middle;text-align:center;">
            {pizza_html}
        </td>
    </tr>
</table>

<!-- DETALHAMENTO -->
<p class="sec-title">Detalhamento das Despesas</p>
<table class="det-table">
    <thead>
        <tr>
            <th style="width:12%">Data</th>
            <th style="width:28%">Fornecedor</th>
            <th style="width:25%">Objeto</th>
            <th style="width:15%">Categoria</th>
            <th class="right" style="width:15%">Valor</th>
        </tr>
    </thead>
    <tbody>
        {linhas_det}
    </tbody>
</table>

<!-- SALDO + ASSINATURA -->
<table width="100%" style="margin-top:14px;">
    <tr>
        <td width="50%" style="vertical-align:top;">
            <div class="saldo-box">
                <div class="saldo-label">Adiantamento Recebido</div>
                <div style="font-size:12px;font-weight:600;color:#0f172a;margin:2px 0 10px 0;">
                    R$ {formatar_br(val_adiantamento_pdf)}
                </div>
                <div class="saldo-label">{label_saldo}</div>
                <div class="saldo-value">R$ {formatar_br(abs(val_saldo_pdf))}</div>
            </div>
        </td>
        <td width="50%" style="text-align:center;vertical-align:bottom;padding-bottom:4px;">
            <div style="margin-top:50px;display:inline-block;width:210px;
                        border-top:1px solid #334155;padding-top:6px;
                        font-size:9px;color:#64748b;text-align:center;">
                {responsavel}<br/>Respons&aacute;vel pelo Caixa
            </div>
        </td>
    </tr>
</table>

</body>
</html>"""

    pdf_bytes = gerar_pdf(html_pdf)

    if pdf_bytes:
        st.success("✅ PDF gerado com sucesso!")
        st.download_button(
            "📥 Baixar Relatório Executivo (PDF)",
            data=pdf_bytes,
            file_name=f"Relatorio_Caixa_{responsavel}_{datetime.now().strftime('%Y%m')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    else:
        st.error("Falha ao gerar o PDF. Verifique se xhtml2pdf está instalado.")
