"""In-memory embedding-similarity cache: if a new question's embedding is
>= threshold cosine-similar to a cached one, reuse its answer instead of
calling the LLM again. Vectors must be L2-normalized so dot product ==
cosine similarity.
"""
import time

import numpy as np

import config


class SimilarityCache:
    def __init__(self, threshold: float = None, ttl_seconds: int = None):
        self.threshold = config.CACHE_SIMILARITY_THRESHOLD if threshold is None else threshold
        self.ttl_seconds = config.CACHE_TTL_SECONDS if ttl_seconds is None else ttl_seconds
        self._entries = []  # list of (vector, value, expires_at)
        self.hits = 0
        self.misses = 0

    def _evict_expired(self):
        now = time.time()
        self._entries = [e for e in self._entries if e[2] > now]

    def get(self, vector):
        self._evict_expired()
        vector = np.asarray(vector, dtype="float32")
        best_sim, best_value = -1.0, None
        for cached_vector, value, _ in self._entries:
            sim = float(np.dot(vector, cached_vector))
            if sim > best_sim:
                best_sim, best_value = sim, value
        if best_sim >= self.threshold:
            self.hits += 1
            return best_value
        self.misses += 1
        return None

    def set(self, vector, value):
        vector = np.asarray(vector, dtype="float32")
        self._entries.append((vector, value, time.time() + self.ttl_seconds))

    def stats(self) -> dict:
        return {"hits": self.hits, "misses": self.misses, "size": len(self._entries)}
