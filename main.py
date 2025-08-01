from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Header
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os, uuid, shutil, tempfile, requests
from dotenv import load_dotenv

from app.processor import extract_pdf_to_text
from app.ingest import process_txt_file
from app.qa import batch_answer

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Mount static under /static instead of /
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")

@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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

@app.post("/hackrx/run")
async def hackrx_run(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    expected_token = os.getenv("HACKRX_AUTH_TOKEN")
    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    url = body.get("url")
    questions = body.get("questions")

    if not url or not questions:
        raise HTTPException(status_code=400, detail="Missing URL or questions.")

    try:
        file_id = str(uuid.uuid4())
        pdf_path = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")
        txt_path = os.path.join(tempfile.gettempdir(), f"{file_id}.txt")

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(pdf_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download file: {str(e)}")

    try:
        extract_pdf_to_text(pdf_path, txt_path)
        process_txt_file(txt_path, f"{file_id}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    try:
        answers = batch_answer(questions, filename_filter=f"{file_id}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM QA failed: {str(e)}")

    return {"answers": answers["answers"]}

