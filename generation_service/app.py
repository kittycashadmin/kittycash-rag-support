# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from generator import Generator, SYSTEM_RULES, format_prompt
from config import TOP_K

app = FastAPI(
    title="Kitty Cash Generation Service",
    description="Generates answers from context using LLM",
    version="1.0.0"
)

generator = Generator()

class Document(BaseModel):
    id: int
    text: str

class GenerateRequest(BaseModel):
    user_query: str
    context: List[Document]

@app.get("/generation/service/health")
def health_check():
    return {"status": "Generation Service running"}


@app.post("/generation/answer/generate")
async def generate_answer(req: GenerateRequest):
    if not req.user_query or not req.context:
        raise HTTPException(status_code=400, detail="user_query and context are required")
    prompt = format_prompt([c.dict() for c in req.context[:TOP_K]], req.user_query)
    try:
        answer = generator.generate(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"answer": answer}


