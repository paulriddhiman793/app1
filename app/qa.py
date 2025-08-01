import os
from dotenv import load_dotenv
from groq import Groq
import lancedb
import pandas as pd

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Initialize DB
def init_db():
    db = lancedb.connect("data1/lancedb")
    return db.open_table("docling")

# Get top-k matching chunks
def get_context(query: str, table, num_results: int = 5, filename_filter: str = None) -> str:
    try:
        search = table.search(query, query_type="vector")
        if filename_filter:
            search = search.where(f"metadata['filename'] == '{filename_filter}'")
        results = search.limit(num_results).to_pandas()
    except Exception as e:
        print(f"[🔍 context search error] {e}")
        return ""

    if results.empty:
        print(f"[⚠️ context] No relevant chunks found for query: '{query}'")
        return ""

    contexts = []
    for _, row in results.iterrows():
        metadata = row.get("metadata", {}) or {}
        filename = metadata.get("filename", "")
        page_numbers = metadata.get("page_numbers", [])
        title = metadata.get("title", "")

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

# Get answer from Groq
def get_answer(question: str, context: str) -> str:
    if not context.strip():
        return "⚠️ I don't know. No relevant context was found in the document."

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

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[❌ LLM error] {e}")
        return "⚠️ Failed to get an answer from the language model. Please try again."

# Batch QA (now uses individual context for each question)
def batch_answer(questions: list[str], filename_filter: str = None) -> dict:
    table = init_db()
    answers = []

    for question in questions:
        context = get_context(question, table, num_results=10, filename_filter=filename_filter)

        if not context:
            answers.append("⚠️ I don't know. No relevant context was found in the document.")
        else:
            answers.append(get_answer(question, context))

    return {"answers": answers}
