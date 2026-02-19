from reportlab.pdfgen import canvas
import os

NOME_ARQUIVO = "teste_oficial.pdf"

print(f"Criando {NOME_ARQUIVO}...")

try:
    c = canvas.Canvas(NOME_ARQUIVO)
    c.setFont("Helvetica", 12)
    
    # Escrevendo conteúdo de texto real
    c.drawString(50, 800, "RELATÓRIO CONFIDENCIAL - PROJETO ALEA-LUMEN")
    c.drawString(50, 780, "---------------------------------------------")
    c.drawString(50, 750, "Este documento serve para validar o MVP.")
    c.drawString(50, 730, "A senha secreta de acesso é: GIRASSOL.")
    c.drawString(50, 710, "A meta para o Q1 é entregar o projeto em 4 dias.")
    c.drawString(50, 690, "Fim do documento.")
    
    c.save()
    print(f"✅ Sucesso! O arquivo '{NOME_ARQUIVO}' foi criado na raiz.")
    print("Agora faça o upload DESTE arquivo na tela do Streamlit.")

except Exception as e:
    print(f"❌ Erro ao criar PDF: {e}")