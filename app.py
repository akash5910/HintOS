from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tutor import Tutor
from llm.client import local_model_status
from problems.bankers import calculate_need, safe_sequence

BASE_DIR = Path(__file__).parent
app = FastAPI(title="HintOS")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
tutor = Tutor(BASE_DIR)


class Message(BaseModel):
    text: str


class BankerInput(BaseModel):
    available: list[int]
    maximum: list[list[int]]
    allocation: list[list[int]]


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.post("/chat")
def chat(message: Message):
    return tutor.reply(message.text)


@app.post("/reset")
def reset():
    return tutor.reset()


@app.get("/history")
def history():
    return {"attempts": tutor.history()}


@app.get("/conversation")
def conversation():
    return {"turns": tutor.conversation()}


@app.get("/status")
def status():
    return local_model_status()


@app.post("/bankers")
def bankers(data: BankerInput):
    try:
        need = calculate_need(data.maximum, data.allocation)
        safe = safe_sequence(data.available, data.maximum, data.allocation)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"need": need, "safe": safe}
