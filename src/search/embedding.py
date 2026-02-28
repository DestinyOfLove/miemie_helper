"""Embedding 模型封装：fastembed + BAAI/bge-small-zh-v1.5。"""

import numpy as np
from fastembed import TextEmbedding

from src.config import EMBEDDING_DIMENSION, EMBEDDING_MODEL_NAME, MODEL_DIR, ensure_dirs

_model: TextEmbedding | None = None


def get_embedding_model() -> TextEmbedding:
    """延迟初始化 embedding 模型（单例）。"""
    global _model
    if _model is None:
        ensure_dirs()
        _model = TextEmbedding(
            model_name=EMBEDDING_MODEL_NAME,
            cache_dir=str(MODEL_DIR),
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
    embeddings = list(model.embed(texts, batch_size=batch_size))
    return np.array(embeddings)


def encode_query(query: str) -> np.ndarray:
    """编码搜索查询。fastembed 内置 query 前缀处理。"""
    model = get_embedding_model()
    embeddings = list(model.query_embed(query))
    return np.array(embeddings[0])
