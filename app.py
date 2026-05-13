import streamlit as st
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
