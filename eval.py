import streamlit as st
from PyPDF2 import PdfReader

def extract_subject(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            for line in text.split("\n"):
                if line.strip().startswith("Subject:"):
                    return line.split(":")[1].strip()
    return None

st.title("Extract Subject from PDF")
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file:
    subject = extract_subject(uploaded_file)
    if subject:
        st.write(f"**Subject Name:** {subject}")
    else:
        st.error("Subject not found in the PDF.")
