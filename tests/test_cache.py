import numpy as np

import cache as cache_module
from cache import SimilarityCache


def test_cache_returns_none_when_empty():
    sim_cache = SimilarityCache(threshold=0.95, ttl_seconds=60)
    assert sim_cache.get(np.array([1.0, 0.0])) is None


def test_cache_hit_for_similar_vector():
    sim_cache = SimilarityCache(threshold=0.95, ttl_seconds=60)
    vector = np.array([1.0, 0.0], dtype="float32")
    sim_cache.set(vector, {"answer": "cached"})
    assert sim_cache.get(vector)["answer"] == "cached"


def test_cache_miss_for_dissimilar_vector():
    sim_cache = SimilarityCache(threshold=0.95, ttl_seconds=60)
    sim_cache.set(np.array([1.0, 0.0], dtype="float32"), {"answer": "cached"})
    assert sim_cache.get(np.array([0.0, 1.0], dtype="float32")) is None


def test_cache_expires_after_ttl(monkeypatch):
    current = [1000.0]
    monkeypatch.setattr(cache_module.time, "time", lambda: current[0])

    sim_cache = SimilarityCache(threshold=0.95, ttl_seconds=5)
    vector = np.array([1.0, 0.0], dtype="float32")
    sim_cache.set(vector, {"answer": "cached"})

    current[0] += 10  # advance past TTL
    assert sim_cache.get(vector) is None


def test_cache_stats_tracks_hits_and_misses():
    sim_cache = SimilarityCache(threshold=0.95, ttl_seconds=60)
    vector = np.array([1.0, 0.0], dtype="float32")
    sim_cache.set(vector, {"answer": "cached"})

    sim_cache.get(vector)  # hit
    sim_cache.get(np.array([0.0, 1.0], dtype="float32"))  # miss

    stats = sim_cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
