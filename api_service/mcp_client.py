# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import json
import logging
import subprocess
from typing import Dict, Any, List, Optional
from fastmcp import Client
from config import MCP_SERVER_URL, MCP_META_URL, TOP_K, OLLAMA_ROUTER_MODEL

logger = logging.getLogger("mcp_client")
logger.setLevel(logging.INFO)

TOOL_MANIFEST_CACHE: Optional[List[Dict[str, Any]]] = None

class RouterError(RuntimeError):
    pass

class KittyCashMCPClient:
    def __init__(self, server_url: str = None, meta_url: str = None):
        self.server_url = server_url or MCP_SERVER_URL
        self.meta_url = meta_url or MCP_META_URL

    async def discover_tools(self, refresh: bool = False) -> List[Dict[str, Any]]:
        global TOOL_MANIFEST_CACHE
        if TOOL_MANIFEST_CACHE and not refresh:
            return TOOL_MANIFEST_CACHE

        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.meta_url}/mcp/tools", timeout=120.0)
            resp.raise_for_status()
            data = resp.json()
        tools = data.get("tools", [])
        TOOL_MANIFEST_CACHE = tools
        logger.info(f"Discovered tools: {[t['name'] for t in tools]}")
        return tools

    def build_router_prompt(self, user_input: str) -> str:
        tools = TOOL_MANIFEST_CACHE or []
        tools_text = ""
        for t in tools:
            caps = ",".join(t.get("capabilities", []))
            desc = t.get("description", "").replace("\n", " ")
            tools_text += f"- name: {t['name']}\n  capabilities: {caps}\n  description: {desc}\n\n"

        prompt = f"""
You are a deterministic tool routing planner for Kitty Cash.

You will receive a user request and a list of available tools.
Return ONLY valid JSON in the format:
{{
  "plan":[
     {{"id":"step1","tool":"<tool_name>","args":{{...}}}},
     {{"id":"step2","tool":"<tool_name>","args":{{...}}}}
  ]
}}
Rules:
1. Your goal is to produce a final natural language answer for the user.
2. If the request needs information retrieval (facts, who/what/when/where/how, product details, etc.),
   - First call the `retriever` tool with the user's query.
   - Never send the retriever's raw results as the final answer.
   - After retrieving, ALWAYS plan a second step that calls the `generator`
     with:
       - `"user_query"` = the original user question
       - `"context"`    = the retriever's results (use `"context_from":"<retriever_step_id>"` to signal chaining).
3. If the request is pure generation (writing, summarization, creative tasks) and no retrieval is needed,
   - Call only the `generator` with `"user_query"`.
4. Call the `indexer` ONLY when a knowledge-base file (`kb_file`) is explicitly mentioned.
5. Produce exactly the JSON plan—no commentary, no markdown.



Available tools:
{tools_text}
User request:
{user_input}
""".strip()
        logger.info(f"Router prompt built for user input: {user_input!r}")
        return prompt

    def call_router_llm(self, prompt: str, timeout_s: int = 300) -> Dict[str, Any]:
        cmd = ["ollama", "run", OLLAMA_ROUTER_MODEL]
        proc = subprocess.run(cmd, input=prompt.encode("utf-8"),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_s)
        out = proc.stdout.decode("utf-8", errors="ignore").strip()

        logger.info(f"Router LLM raw output: {out[:500]}")

        start = out.find("{")
        end = out.rfind("}")
        if start == -1 or end == -1:
            raise RouterError(f"Router LLM did not return any JSON. Raw: {out}")

        try:
            plan = json.loads(out[start:end+1])
            logger.info(f"Router LLM parsed plan successfully")
            return plan
        except json.JSONDecodeError as e:
            raise RouterError(f"Router LLM returned invalid JSON. Raw: {out}. Error: {e}")

    async def call_tool(self, tool_name: str, args: Dict[str, Any], timeout: float = 300.0):
        logger.info(f"Calling tool '{tool_name}' with args: {args}")
        async with Client(self.server_url, timeout=timeout) as client:
            res = await client.call_tool(tool_name, args)
            data = getattr(res, "data", None)
            if data:
                logger.info(f"Tool '{tool_name}' returned data with keys: {list(data.keys())}")
                return data
            content = getattr(res, "content", None)
            if content and len(content) > 0 and hasattr(content[0], "text"):
                try:
                    parsed = json.loads(content[0].text)
                    logger.info(f"Tool '{tool_name}' returned parseable JSON content")
                    return parsed
                except Exception:
                    logger.warning(f"Tool '{tool_name}' returned non-JSON content")
                    return {"text": content[0].text}
            logger.warning(f"Tool '{tool_name}' returned empty or unrecognized response")
            return {}

    async def execute_plan(self, plan: List[Dict[str, Any]]):
        outputs = {}
        for step in plan:
            step_id = step["id"]
            tool = step["tool"]
            args = dict(step.get("args", {}))

            if "context_from" in args:
                ref = args.pop("context_from")
                prev = outputs.get(ref, {})
                context_docs = []
                if isinstance(prev, dict):
                    results = prev.get("results", [])
                    for d in results:
                        if isinstance(d, dict):
                            context_docs.append(d.get("document") or d.get("text") or str(d))
                        else:
                            context_docs.append(str(d))
                elif isinstance(prev, list):
                    context_docs = [str(d) for d in prev]
                args["context"] = context_docs

            logger.info(f"Executing plan step '{step_id}' using tool '{tool}' with args keys: {list(args.keys())}")
            outputs[step_id] = await self.call_tool(tool, args)
            logger.info(f"Step '{step_id}' output keys: {list(outputs[step_id].keys()) if isinstance(outputs[step_id], dict) else 'unknown'}")

        return outputs

    async def route_and_call(self, user_input: str, kb_file: str = None):
        tools = await self.discover_tools()
        global TOOL_MANIFEST_CACHE
        TOOL_MANIFEST_CACHE = tools

        plan = [
            {"id": "retr1", "tool": "retriever", "args": {"query": user_input}},
            {"id": "gen1", "tool": "generator", "args": {"user_query": user_input, "context_from": "retr1"}}
        ]

        outputs = await self.execute_plan(plan)
        last_step = plan[-1]["id"] if plan else None
        final_answer = outputs.get(last_step, {}).get("answer") if last_step else ""
        logger.info(f"Final answer returned: {final_answer[:240] if final_answer else '<empty>'}")

        return {"route": {"plan": plan}, "outputs": outputs, "answer": final_answer}

    async def retrieve(self, query: str):
        return await self.call_tool("retriever", {"query": query})

    async def generate(self, user_query: str, context: list):
        return await self.call_tool("generator", {"user_query": user_query, "context": context})

    async def index(self, kb_file: str):
        return await self.call_tool("indexer", {"kb_file": kb_file})