# app/ingest.py

import os
from typing import List
from chunking_evaluation.chunking import ClusterSemanticChunker
from chunking_evaluation.utils import openai_token_count
from lancedb.embeddings import get_registry
import lancedb
import torch

# Connect to LanceDB
db = lancedb.connect("data1/lancedb")

# Embedding model
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

# Define schema
from lancedb.pydantic import LanceModel, Vector
from typing import Optional

class ChunkMetadata(LanceModel):
    filename: Optional[str]
    page_numbers: List[int]
    title: Optional[str]

class Chunks(LanceModel):
    text: str = embedding_func_obj.SourceField()
    vector: Vector(embedding_func_obj.ndims()) = embedding_func_obj.VectorField()  # type: ignore
    metadata: ChunkMetadata

# Initialize table (create once, overwrite for now)
table = db.create_table("docling", schema=Chunks, mode="overwrite")

def process_txt_file(txt_path: str, filename: str):
    # Read the full document
    with open(txt_path, "r", encoding="utf-8") as f:
        document = f.read()

    # Chunk using your semantic chunker
    cluster_chunker = ClusterSemanticChunker(
        embedding_function=callable_embedding_func,
        max_chunk_size=400,
        length_function=openai_token_count
    )
    chunk_texts = cluster_chunker.split_text(document)

    # Wrap into LanceDB format
    processed = [
        {
            "text": chunk_text,
            "metadata": {
                "filename": filename,
                "page_numbers": [],  # not inferable at this stage
                "title": None
            }
        }
        for chunk_text in chunk_texts
    ]

    table.add(processed)
    print("✅ Inserted into LanceDB:", len(processed), "chunks")
