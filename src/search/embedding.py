"""Embedding 模型封装：sentence-transformers + BAAI/bge-small-zh-v1.5。"""

import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import EMBEDDING_DIMENSION, EMBEDDING_MODEL_NAME, MODEL_DIR, ensure_dirs

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """延迟初始化 embedding 模型（单例）。"""
    global _model
    if _model is None:
        ensure_dirs()
        _model = SentenceTransformer(
            EMBEDDING_MODEL_NAME,
            cache_folder=str(MODEL_DIR),
            device="cpu",
        )
    return _model


def ensure_model_available() -> bool:
    """检查模型是否已缓存到本地。"""
    model_cache = MODEL_DIR / f"models--{EMBEDDING_MODEL_NAME.replace('/', '--')}"
    return model_cache.exists()


def encode_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """批量编码文本为向量。返回 shape (N, EMBEDDING_DIMENSION)。"""
    if not texts:
        return np.empty((0, EMBEDDING_DIMENSION))
    model = get_embedding_model()
    return model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )


def encode_query(query: str) -> np.ndarray:
    """编码搜索查询。BGE 模型对查询使用 'query: ' 前缀。"""
    model = get_embedding_model()
    prefixed = f"query: {query}"
    return model.encode(
        prefixed,
        normalize_embeddings=True,
    )
