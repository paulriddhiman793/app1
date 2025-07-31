from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List
import os, uuid, shutil

from app.processor import extract_pdf_to_text
from app.ingest import process_txt_file
from app.qa import batch_answer

app = FastAPI()
UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    txt_path = os.path.join(UPLOAD_DIR, f"{file_id}.txt")

    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    extract_pdf_to_text(pdf_path, txt_path)
    process_txt_file(txt_path, f"{file_id}.pdf")

    return {"message": "PDF processed", "file_id": file_id}

@app.post("/ask/")
async def ask_question(question: str = Form(...), file_id: str = Form(...)):
    answers = batch_answer([question], filename_filter=f"{file_id}.pdf")
    return JSONResponse(content={"question": question, "answer": answers["answers"][0]})

@app.post("/batch-ask/")
async def ask_batch(questions: List[str], file_id: str):
    answers = batch_answer(questions, filename_filter=f"{file_id}.pdf")
    return answers
