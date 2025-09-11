import subprocess
from config import LLM_MODEL


SYSTEM_RULES = """
You are a specialized Virtual Assistant for Kittycash workflows.
Use ONLY the retrieved context to answer.

Rules:
- If the information is present in the retrieved context, answer clearly and concisely.
- Do NOT mention or reference document IDs, source identifiers, or any internal metadata in your responses.
- If the context does not provide enough details, ask ONE short clarifying question, without referencing documents.
- Never generate or assume fees, amounts, policies, or member data.
- Keep responses professional, trustworthy, and compliant with financial communication standards.
- If a query asks for information outside the retrieved context, state that it is not available and ask a clarifying question.
- get me answers as granular as possible
- don't mention retrieved context
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
    def __init__(self, model: str = LLM_MODEL):
        self.model = model

    def generate(self, prompt: str) -> str:
        result = subprocess.run(
            ["ollama", "run", self.model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            raise RuntimeError(f"LLM generation failed: {result.stderr.decode('utf-8')}")
        return result.stdout.decode("utf-8").strip()
