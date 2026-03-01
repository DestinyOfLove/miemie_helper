"""ChromaDB 向量存储：文档分块、嵌入存储、相似度检索。"""

import chromadb
import numpy as np

from src.config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, ensure_dirs

_chroma_client: chromadb.ClientAPI | None = None

COLLECTION_NAME = "doc_chunks"


def get_chroma_client() -> chromadb.ClientAPI:
    """获取 ChromaDB 持久化客户端（单例）。"""
    global _chroma_client
    if _chroma_client is None:
        ensure_dirs()
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma_client


def get_collection() -> chromadb.Collection:
    """获取或创建文档分块集合。"""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def chunk_document(doc_id: str, text: str, metadata: dict) -> list[dict]:
    """将文档文本分块。返回 [{chunk_id, doc_id, text, metadata}, ...]。"""
    if not text.strip():
        return []

    chunks = []
    paragraphs = text.split("\n")
    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 1 > CHUNK_SIZE:
            if current_chunk:
                chunks.append(_make_chunk(doc_id, current_chunk, metadata, chunk_index))
                chunk_index += 1
                # 保留尾部重叠
                overlap = current_chunk[-CHUNK_OVERLAP:] if len(current_chunk) > CHUNK_OVERLAP else ""
                current_chunk = (overlap + "\n" + para).strip()
            else:
                # 单段落超长，强制切分
                for i in range(0, len(para), CHUNK_SIZE - CHUNK_OVERLAP):
                    sub = para[i:i + CHUNK_SIZE]
                    chunks.append(_make_chunk(doc_id, sub, metadata, chunk_index))
                    chunk_index += 1
                current_chunk = ""
        else:
            current_chunk = (current_chunk + "\n" + para).strip()

    if current_chunk.strip():
        chunks.append(_make_chunk(doc_id, current_chunk, metadata, chunk_index))

    return chunks


def _make_chunk(doc_id: str, text: str, metadata: dict, chunk_index: int) -> dict:
    """构造单个分块记录。"""
    return {
        "chunk_id": f"{doc_id}_chunk_{chunk_index}",
        "doc_id": doc_id,
        "text": text,
        "metadata": {**metadata, "doc_id": doc_id, "chunk_index": chunk_index},
    }


def add_document_chunks(chunks: list[dict], embeddings: np.ndarray) -> None:
    """将文档分块及其嵌入向量存入 ChromaDB。"""
    if not chunks:
        return
    collection = get_collection()
    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings.tolist(),
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )


def delete_document_chunks(doc_id: str) -> None:
    """删除某文档的所有分块。"""
    collection = get_collection()
    # 查找所有属于该文档的分块
    results = collection.get(where={"doc_id": doc_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def search_similar(query_embedding: np.ndarray) -> dict:
    """向量相似度检索。返回所有匹配的 ChromaDB 查询结果。"""
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    actual_n = count
    return collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"],
    )
