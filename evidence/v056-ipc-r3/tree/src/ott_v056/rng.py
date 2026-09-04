"""D19: replicate SHA-256 digest → NumPy SeedSequence → 128 probe streams."""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np

STREAM_SAMPLER = 0
STREAM_GROUND = 1
STREAM_PATH = 2
N_PROBES = 128
ENTROPY_WORDS = 8
RUNTIME_NUMPY_VERSION = "2.2.0"


class RngError(RuntimeError):
    pass


def digest_to_entropy_words(digest: bytes) -> List[int]:
    if len(digest) != 32:
        raise RngError("replicate digest must be 32 bytes")
    return [int.from_bytes(digest[i : i + 4], "big") for i in range(0, 32, 4)]


def replicate_seed_sequence(digest: bytes) -> np.random.SeedSequence:
    return np.random.SeedSequence(digest_to_entropy_words(digest))


def spawn_probe_sequences(digest: bytes) -> List[np.random.SeedSequence]:
    return list(replicate_seed_sequence(digest).spawn(N_PROBES))


def probe_stream_sequences(
    probe_ss: np.random.SeedSequence,
) -> Tuple[np.random.SeedSequence, np.random.SeedSequence, np.random.SeedSequence]:
    sampler_ss, ground_ss, path_ss = probe_ss.spawn(3)
    return sampler_ss, ground_ss, path_ss


def probe_generators(probe_ss: np.random.SeedSequence) -> Tuple[np.random.Generator, np.random.Generator, np.random.Generator]:
    sampler_ss, ground_ss, path_ss = probe_stream_sequences(probe_ss)
    return (
        np.random.default_rng(sampler_ss),
        np.random.default_rng(ground_ss),
        np.random.default_rng(path_ss),
    )


def generators_for_probe(digest: bytes, probe_index: int) -> Tuple[np.random.Generator, np.random.Generator, np.random.Generator]:
    if probe_index < 0 or probe_index >= N_PROBES:
        raise RngError("probe_index must be 0..127")
    return probe_generators(spawn_probe_sequences(digest)[probe_index])


def spawn_key_list(ss: np.random.SeedSequence) -> List[int]:
    return [int(x) for x in ss.spawn_key]


def first_draws(rng: np.random.Generator) -> dict:
    """Deterministic first draws used only as sentinel identity, not as science."""
    u32 = int(rng.integers(0, 2**32, dtype=np.uint32))
    u01 = float(rng.random())
    return {"integers_uint32": u32, "random_float64": u01}


def require_runtime_numpy(version: str | None = None) -> None:
    found = np.__version__
    expected = version or RUNTIME_NUMPY_VERSION
    if found != expected:
        raise RngError(
            f"NumPy {found} is not the frozen runtime version {expected}"
        )
