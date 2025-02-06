import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import re
from sentence_transformers import SentenceTransformer, util
import fitz  
import os
from rapidfuzz import fuzz


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)  
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"  
    return text


def extract_roll_number(text):
    match = re.search(r'Roll Number:\s*(\d+)', text)  
    return match.group(1) if match else "Unknown" 

def calculate_similarity(answer1, answer2):
    return fuzz.ratio(str(answer1), str(answer2))  

def assign_marks(similarity, total_marks):
    if similarity >= 90:
        return total_marks 
    elif similarity >= 70:
        return total_marks * 0.75  
    elif similarity >= 50:
        return total_marks * 0.50 
    else:
        return 0  

def extract_questions_answers(pdf_text):
    lines = pdf_text.split("\n")  
    questions = []
    answers = []
    current_question = None
    current_answer = ""

    for line in lines:
        line = line.strip()
        if line.startswith("Q "): 
            if current_question:
                questions.append(current_question)
                answers.append(current_answer.strip())  
            current_question = line  
            current_answer = ""
        elif current_question: 
            current_answer += " " + line

    if current_question:
        questions.append(current_question)
        answers.append(current_answer.strip())

    return questions, answers

def extract_question_number(question):
    match = re.search(r'Q\s?\d+', question)  
    if match:
        q_number = match.group(0).replace(" ", "")  
        question_text = re.sub(r'Q\s?\d+', '', question).strip()  
        return q_number, question_text
    return None, question  

def clean_answer_column(answer):
    return answer.replace('Answer: ', '').strip()


def main():
    st.title("Student Answer Evaluation System")

    # File upload for correct answers
    correct_answers_file = st.file_uploader("Upload Correct Answers File", type=["xlsx"])
    if correct_answers_file is not None:
        correct_answers = pd.read_excel(correct_answers_file)
        st.write("Correct Answers:", correct_answers)

    # File upload for student answers
    student_pdf = st.file_uploader("Upload Student's Answer PDF", type=["pdf"])
    if student_pdf is not None and correct_answers_file is not None:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(student_pdf)

        # Extract questions and answers
        questions, answers = extract_questions_answers(pdf_text)

        roll_number = extract_roll_number(pdf_text)

        student_answers = pd.DataFrame({'Question': questions, 'Answers': answers})

        # Extract question number
        student_answers[['No', 'Question']] = student_answers['Question'].apply(lambda x: pd.Series(extract_question_number(x)))
        
        # Clean answers
        student_answers['Answers'] = student_answers['Answers'].apply(clean_answer_column)

        # Merge with correct answers
        df_merged = pd.merge(student_answers, correct_answers, on='No', suffixes=('_student', '_correct'))
        
        # Calculate similarity
        df_merged['Similarity (%)'] = df_merged.apply(lambda row: calculate_similarity(row['Answers_student'], row['Answers_correct']), axis=1)
        
        # Assign marks based on similarity
        df_merged['Assigned Marks'] = df_merged.apply(lambda row: assign_marks(row['Similarity (%)'], row['Marks']), axis=1)

        student_answers = student_answers.merge(df_merged[['No', 'Assigned Marks']], on='No', how='left')

        # Total marks obtained
        total_marks_obtained = df_merged['Assigned Marks'].sum()
        total_possible_marks = correct_answers['Marks'].sum()

        # Display total marks
        st.write(f"Student's Total Marks {roll_number}: {total_marks_obtained:.2f} out of {total_possible_marks:.2f}")
        st.write(f"Roll Number: {roll_number}")

        # Extract subject name
        with open(student_pdf, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            subject_name = next((line.split(":")[1].strip() for line in text.split("\n") if "Subject :" in line), "Unknown")

        st.write(f"Subject Name: {subject_name}")

        # Display student answers with assigned marks
        st.write(student_answers)

        # Download the results as a CSV file
        student_answers_csv = student_answers.to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=student_answers_csv,
            file_name="student_answers_with_marks.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()
