import streamlit as st
import pandas as pd
import re
import fitz  
from rapidfuzz import fuzz

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")  # Read file from memory
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

def extract_roll_number(text):
    match = re.search(r'Roll Number:\s*(\d+)', text)
    return match.group(1) if match else "Unknown"

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

st.title("Student Answer Grading System")

pdf_file = st.file_uploader("Upload Student's Answer PDF", type=["pdf"])
csv_file = st.file_uploader("Upload Correct Answers CSV", type=["csv"])

if pdf_file and csv_file:
    correct_answers = pd.read_csv(csv_file)
    pdf_text = extract_text_from_pdf(pdf_file)
    questions, answers = extract_questions_answers(pdf_text)
    roll_number = extract_roll_number(pdf_text)
    
    student_answers = pd.DataFrame({'Question': questions, 'Answers': answers})
    student_answers[['No', 'Question']] = student_answers['Question'].apply(lambda x: pd.Series(extract_question_number(x)))
    student_answers['Answers'] = student_answers['Answers'].apply(clean_answer_column)
    
    df_merged = pd.merge(student_answers, correct_answers, on='No', suffixes=('_student', '_correct'))
    df_merged['Similarity (%)'] = df_merged.apply(lambda row: calculate_similarity(row['Answers_student'], row['Answers_correct']), axis=1)
    df_merged['Assigned Marks'] = df_merged.apply(lambda row: assign_marks(row['Similarity (%)'], row['Marks']), axis=1)
    
    student_answers = student_answers.merge(df_merged[['No', 'Assigned Marks']], on='No', how='left')
    total_marks_obtained = df_merged['Assigned Marks'].sum()
    total_possible_marks = correct_answers['Marks'].sum()
    
    st.write(f"**Student Roll Number:** {roll_number}")
    st.write(f"**Total Marks Obtained:** {total_marks_obtained:.2f} out of {total_possible_marks:.2f}")
    
    st.dataframe(student_answers)
    
    csv_output = student_answers.to_csv(index=False).encode('utf-8')
    st.download_button("Download Graded CSV", csv_output, "graded_answers.csv", "text/csv")
