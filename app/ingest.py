# app/ingest.py

import os
from typing import List, Optional
from chunking_evaluation.chunking import ClusterSemanticChunker
from chunking_evaluation.utils import openai_token_count
from lancedb.embeddings import get_registry
import lancedb
import torch

# LanceDB connection
db = lancedb.connect("data1/lancedb")

# Embedding model setup
embedding_func_obj = (
    get_registry()
    .get("sentence-transformers")
    .create(
        name="thenlper/gte-large",
        device="cuda" if torch.cuda.is_available() else "cpu",
        normalize_embeddings=True,
        batch_size=64,
    )
)

def callable_embedding_func(texts: List[str]) -> List[List[float]]:
    return embedding_func_obj.generate_embeddings(texts)

# LanceDB schema
from lancedb.pydantic import LanceModel, Vector

class ChunkMetadata(LanceModel):
    filename: Optional[str]
    page_numbers: List[int]
    title: Optional[str]

class Chunks(LanceModel):
    text: str = embedding_func_obj.SourceField()
    vector: Vector(embedding_func_obj.ndims()) = embedding_func_obj.VectorField()  # type: ignore
    metadata: ChunkMetadata

# Create or overwrite table
table = db.create_table("docling", schema=Chunks, mode="overwrite")

# Main processor
def process_txt_file(txt_path: str, filename: str):
    # Read text file content
    with open(txt_path, "r", encoding="utf-8") as f:
        document = f.read().strip()

    if not document:
        raise ValueError("❌ Extracted document text is empty. Cannot proceed.")

    # Chunking
    cluster_chunker = ClusterSemanticChunker(
        embedding_function=callable_embedding_func,
        max_chunk_size=400,
        length_function=openai_token_count
    )
    chunk_texts = cluster_chunker.split_text(document)

    if not chunk_texts:
        raise ValueError("❌ No valid chunks generated from the document.")

    # Wrap chunks into LanceDB format
    processed = [
        {
            "text": chunk_text,
            "metadata": {
                "filename": filename,
                "page_numbers": [],
                "title": None
            }
        }
        for chunk_text in chunk_texts
    ]

    table.add(processed)
    print("✅ Inserted into LanceDB:", len(processed), "chunks")
