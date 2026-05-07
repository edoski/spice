from __future__ import annotations

from typing import Any

import pytest

from spice.core.errors import StateLayoutError
from spice.storage.corpus_codecs import ACQUIRE_RUN_CODEC, DATASET_MANIFEST_CODEC
from spice.storage.payloads import PayloadCodec


@pytest.mark.parametrize(
    ("codec", "match"),
    [
        (DATASET_MANIFEST_CODEC, "dataset manifest"),
        (ACQUIRE_RUN_CODEC, "acquire run"),
    ],
)
def test_corpus_codecs_bind_storage_error_labels(
    codec: PayloadCodec[Any],
    match: str,
) -> None:
    with pytest.raises(StateLayoutError, match=match):
        codec.decode({"unexpected": 1})
