# pyright: strict

"""Strict payload codecs for corpus-root manifests and acquire runs."""

from __future__ import annotations

from ..corpus.metadata import AcquireRunRecord, CorpusManifest
from .payloads import PayloadCodec, pydantic_model_codec

DATASET_MANIFEST_CODEC: PayloadCodec[CorpusManifest] = pydantic_model_codec(
    "corpus manifest",
    CorpusManifest,
)
ACQUIRE_RUN_CODEC: PayloadCodec[AcquireRunRecord] = pydantic_model_codec(
    "acquire run",
    AcquireRunRecord,
)
