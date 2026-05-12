import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestão de Caixa | M e Lopes", layout="wide")

# --- BANCO DE DADOS TEMPORÁRIO DE CLIENTES ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = {
        "Wellington Rafael": {"pix": "014.565.671-36", "banco": "Santander"},
        "G.A Solar (Geral)": {"pix": "CNPJ: 66.283.560/0001-09", "banco": "PJ Bank"}
    }

# --- BARRA LATERAL (GESTÃO DE CLIENTES) ---
with st.sidebar:
    st.title("M e Lopes")
    st.subheader("Painel de Controle")
    
    # Seleção de Cliente/Obra
    cliente_selecionado = st.selectbox("Selecione o Cliente/Obra", options=list(st.session_state.clientes.keys()))
    
    st.divider()
    
    # Inclusão de Novo Cliente
    st.write("### + Incluir Novo Cliente")
    novo_nome = st.text_input("Nome do Cliente/Func.")
    novo_pix = st.text_input("Chave PIX")
    novo_banco = st.text_input("Banco")
    
    if st.button("Salvar Novo Cliente"):
        if novo_nome:
            st.session_state.clientes[novo_nome] = {"pix": novo_pix, "banco": novo_banco}
            st.success("Cliente adicionado!")
            st.rerun()

# --- INTERFACE PRINCIPAL ---
st.title(f"Caixa de Obra: {cliente_selecionado}")
st.info(f"Dados Atuais: {st.session_state.clientes[cliente_selecionado]['banco']} | PIX: {st.session_state.clientes[cliente_selecionado]['pix']}")

# 1. ENTRADA DE DADOS
adiantamento = st.number_input("Valor do Adiantamento (R$)", min_value=0.0, step=100.0)

st.write("### Lançamentos de Despesas")
if 'despesas' not in st.session_state:
    st.session_state.despesas = pd.DataFrame(columns=["Data", "Objeto", "Valor (R$)", "Centro de Custos"])

despesas_editadas = st.data_editor(
    st.session_state.despesas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f", min_value=0.0),
        "Centro de Custos": st.column_config.SelectboxColumn(
            options=["Vale alimentação", "Combustível", "Canteiro de obras", "Material Elétrico", "Despesas com viagem"]
        )
    }
)

arquivos_anexados = st.file_uploader("Anexar Comprovantes", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

# 2. CÁLCULOS
total_gasto = despesas_editadas["Valor (R$)"].sum()
saldo = total_gasto - adiantamento
status_caixa = "CAIXA ZERADO"
if saldo > 0: status_caixa = f"A REEMBOLSAR: R$ {saldo:,.2f}"
elif saldo < 0: status_caixa = f"SALDO EM CAIXA: R$ {abs(saldo):,.2f}"

colA, colB, colC = st.columns(3)
colA.metric("Total Gasto", f"R$ {total_gasto:,.2f}")
colB.metric("Adiantamento", f"R$ {adiantamento:,.2f}")
colC.metric("Resultado", status_caixa)

# 3. EXPORTAÇÃO
tabela_html = despesas_editadas.to_html(index=False, border=1, justify="center")
lista_anexos = "".join([f"<li>{arq.name}</li>" for arq in arquivos_anexados]) if arquivos_anexados else "Nenhum"

relatorio_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        .header {{ border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th {{ background-color: #f2f2f2; padding: 8px; border: 1px solid #ddd; }}
        td {{ padding: 8px; border: 1px solid #ddd; text-align: center; }}
        .footer {{ margin-top: 50px; padding-top: 10px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 10pt; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>CAIXA DE OBRA - {cliente_selecionado.upper()}</h2>
        <p>G.A SOLAR | Emitido em: {datetime.now().strftime("%d/%m/%Y")}</p>
    </div>
    <p><strong>PIX:</strong> {st.session_state.clientes[cliente_selecionado]['pix']} | <strong>Banco:</strong> {st.session_state.clientes[cliente_selecionado]['banco']}</p>
    <p><strong>Adiantamento:</strong> R$ {adiantamento:,.2f}</p>
    
    {tabela_html}
    
    <h3 style="text-align: right;">Total Gasto: R$ {total_gasto:,.2f}</h3>
    <h4 style="text-align: right;">{status_caixa}</h4>
    
    <div style="font-size: 8pt;"><strong>Anexos:</strong> <ul>{lista_anexos}</ul></div>
    
    <div class="footer">
        <strong>M e Lopes, assessoria em tecnologia</strong><br>
        Soluções Digitais para Engenharia e Agronegócio
    </div>
</body>
</html>
"""

st.download_button("📄 Gerar Relatório M e Lopes", data=relatorio_html, file_name=f"Caixa_{cliente_selecionado}.html", mime="text/html")

# --- RODAPÉ DA PÁGINA ---
st.markdown("---")
st.caption("M e Lopes, assessoria em tecnologia")
