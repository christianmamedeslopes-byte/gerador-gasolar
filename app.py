import streamlit as st

# Configuração da Aba do Navegador
st.set_page_config(page_title="M e Lopes | G.A Solar", page_icon="☀️")

# Cabeçalho do Sistema
st.title("M e Lopes Assessoria")
st.subheader("Sistema de Gestão: Caixa de Obra - G.A Solar")

# Formulário de Entrada (Inputs)
st.write("### 1. Dados do Cliente")
cliente = st.text_input("Nome ou Razão Social do Cliente")
cidade = st.text_input("Cidade da Instalação")

st.write("### 2. Dados Financeiros (R$)")
# No Streamlit, number_input trava a digitação para aceitar apenas números (Evita erros de usuário)
valor_venda = st.number_input("Valor Total da Venda (Contrato)", min_value=0.0, step=100.0)
custo_kit = st.number_input("Custo do Kit Solar (Equipamentos)", min_value=0.0, step=100.0)
custo_mao_obra = st.number_input("Custo de Mão de Obra / Empreiteiro", min_value=0.0, step=100.0)

# O Motor Lógico (Cálculos de DRE)
if st.button("Processar Relatório"):
    if cliente == "":
        st.error("Erro: O nome do cliente é obrigatório.")
    else:
        custo_total = custo_kit + custo_mao_obra
        lucro_bruto = valor_venda - custo_total
        margem = (lucro_bruto / valor_venda) * 100 if valor_venda > 0 else 0
        
        st.success("Dados processados com sucesso!")
        st.write("#### Prévia Financeira:")
        st.write(f"- **Custo Operacional Total:** R$ {custo_total:,.2f}")
        st.write(f"- **Lucro Bruto da Obra:** R$ {lucro_bruto:,.2f}")
        st.write(f"- **Margem de Lucro:** {margem:.1f}%")
        
        st.info("A funcionalidade de exportação para PDF com as logomarcas será inserida na próxima etapa.")
