# app/qa.py

import os
from dotenv import load_dotenv
from groq import Groq
import lancedb

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# LanceDB connection
def init_db():
    db = lancedb.connect("data1/lancedb")
    return db.open_table("docling")

# Hybrid context search
def get_context(query: str, table, num_results: int = 5, filename_filter: str = None) -> str:
    search = table.search(query, query_type="vector")
    if filename_filter:
        search = search.where(f"metadata['filename'] == '{filename_filter}'")
    results = search.limit(num_results).to_pandas()

    contexts = []
    for _, row in results.iterrows():
        filename = row["metadata"].get("filename", "")
        page_numbers = row["metadata"].get("page_numbers", [])
        title = row["metadata"].get("title", "")

        source_parts = []
        if filename:
            source_parts.append(filename)
        if page_numbers:
            source_parts.append(f"p. {', '.join(str(p) for p in page_numbers)}")

        source = f"\nSource: {' - '.join(source_parts)}"
        if title:
            source += f"\nTitle: {title}"

        contexts.append(f"{row['text']}{source}")

    return "\n\n".join(contexts)

# Call Groq LLM
def get_answer(question: str, context: str) -> str:
    system_prompt = f"""You are an intelligent document analysis assistant that answers questions strictly based on insurance policy documents and other official contracts.

Your goal is to return accurate, consistent, and auditable responses that include:
- ✅ A clear and concise **Answer**
- 📘 **Supporting Justification** directly extracted or paraphrased from the document
- 📄 Exact **Clause or Section Reference** where the information is found (e.g., "Section 2.1.3" or "Page 5, Clause 4")

Your outputs must always be:
1. **Factual** — Use only the information present in the given document context.
2. **Interpretable** — Avoid vague language; responses should be usable in compliance, claims, and audits.
3. **Complete** — If the answer involves eligibility, conditions, caps/limits, or timeframes, include them.
4. **Traceable** — Always refer to the relevant clause or section in the document, if available.
5. **Graceful fallback** — If the document lacks relevant information, respond with: "I don't know.".

Context:
{context}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# Single or batch answer
def batch_answer(questions: list[str], filename_filter: str = None) -> dict:
    table = init_db()
    context = get_context("insurance policy document", table, num_results=10, filename_filter=filename_filter)
    answers = [get_answer(q, context) for q in questions]
    return {"answers": answers}
