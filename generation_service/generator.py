# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import subprocess
import os
import json
from config import LLM_MODEL
import requests



SYSTEM_RULES = """
You are a specialized Virtual Assistant for Kittycash workflows.
Use ONLY the retrieved context to answer.

Rules:
- If the information is present in the retrieved context, answer clearly and concisely.
- Answer using ONLY the information provided in the context.
- Do NOT mention or reference document IDs, source identifiers, or any internal metadata in your responses.
- Do NOT generate or assume any information not directly contained in the context.
- If the context does not provide enough details, ask ONE short clarifying question, without referencing documents.
- Never generate or assume fees, amounts, policies, or member data.
- Keep responses professional, trustworthy, and compliant with financial communication standards.
- If a query asks for information outside the retrieved context, state that it is not available and ask a clarifying question.
- get me answers as granular as possible
- don't mention retrieved context
- If the same question is answered in multiple context blocks, always use the latest (most recent) answer provided.


"""

def format_prompt(context_blocks, user_query):
    context_text = "\n\n".join([f"[DOC {c['id']}]\n{c['text']}" for c in context_blocks])
    prompt = f"""{SYSTEM_RULES}

[CONTEXT]
{context_text}

[USER QUESTION]
{user_query}

[ASSISTANT RESPONSE]
"""
    return prompt

class Generator:
    def __init__(self, model: str = None):
        self.model = model or os.environ.get("LLM_MODEL", "llama3:latest")
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://ollama:11434")

    def generate(self, prompt: str) -> str:
        prompt += "\nRespond only with a JSON object: {\"answer\": <your answer>}"
        response = requests.post(
            f"{self.ollama_host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json", 
                "stream": False
            }
        )
        if response.status_code != 200:
            raise RuntimeError(f"LLM generation failed: {response.text}")
        try:
            answer_json = json.loads(response.json()["response"])
            return answer_json.get("answer", "")
        except Exception as e:
            raise RuntimeError(f"Error parsing LLM response: {e}")
