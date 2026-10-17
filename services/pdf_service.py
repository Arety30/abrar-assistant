from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter
import os

class PDFService:
    @staticmethod
    def create_pdf(text, filename="output.pdf"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=text, ln=True, align='L')
        pdf.output(filename)
        return filename

    @staticmethod
    def read_pdf(file_path):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
