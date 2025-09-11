import time
import sqlite3
from .generator import format_prompt


class RAGPipeline:
    def __init__(self, retriever, generator, top_k=5, db_path="data/timings.db"):
        self.retriever = retriever
        self.generator = generator
        self.top_k = top_k
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS query_timings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                retrieval_time REAL,
                prompt_format_time REAL,
                generation_time REAL,
                total_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def ask(self, query: str) -> str:
        start_total = time.time()

        start_emb = time.time()
        hits = self.retriever.retrieve(query, k=self.top_k)
        end_emb = time.time()

        if not hits:
            return "I don't have enough information in the context. Could you clarify your question?"

        start_format = time.time()
        prompt = format_prompt(hits, query)
        end_format = time.time()

        start_gen = time.time()
        answer = self.generator.generate(prompt)
        end_gen = time.time()

        end_total = time.time()

        retrieval_time = end_emb - start_emb
        prompt_format_time = end_format - start_format
        generation_time = end_gen - start_gen
        total_time = end_total - start_total

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO query_timings (query, retrieval_time, prompt_format_time, generation_time, total_time)
            VALUES (?, ?, ?, ?, ?)
        """, (query, retrieval_time, prompt_format_time, generation_time, total_time))
        conn.commit()
        conn.close()

        print(f"Retrieval time: {retrieval_time:.2f} seconds")
        print(f"Prompt formatting time: {prompt_format_time:.2f} seconds")
        print(f"Generation time: {generation_time:.2f} seconds")
        print(f"Total time: {total_time:.2f} seconds")

        return answer
