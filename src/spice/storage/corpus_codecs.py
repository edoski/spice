# pyright: strict

"""Strict payload codecs for corpus-root manifests and acquire runs."""

from __future__ import annotations

from ..corpus.metadata import AcquireRunRecord, DatasetManifest
from .payloads import PayloadCodec, pydantic_model_codec

DATASET_MANIFEST_CODEC: PayloadCodec[DatasetManifest] = pydantic_model_codec(
    "dataset manifest",
    DatasetManifest,
)
ACQUIRE_RUN_CODEC: PayloadCodec[AcquireRunRecord] = pydantic_model_codec(
    "acquire run",
    AcquireRunRecord,
)
