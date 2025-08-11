#!/usr/bin/env python3
"""
Chroma vector store wrapper with SentenceTransformers embeddings
"""

from typing import List, Dict, Any
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, persist_directory: str):
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        # Use new PersistentClient for on-disk storage (Chroma >= 1.0)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="research_articles", metadata={"hnsw:space": "cosine"})
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def add_documents(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        embeddings = self.model.encode(documents, show_progress_bar=False, convert_to_numpy=True).tolist()
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def query(self, query_texts: List[str], n_results: int = 5) -> Dict[str, Any]:
        query_embeddings = self.model.encode(query_texts, show_progress_bar=False, convert_to_numpy=True).tolist()
        return self.collection.query(query_embeddings=query_embeddings, n_results=n_results)



