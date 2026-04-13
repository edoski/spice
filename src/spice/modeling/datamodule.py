"""LightningDataModule for temporal SPICE datasets."""

from __future__ import annotations

import lightning as L

from .representations import PreparedRepresentation, PreparedRepresentationLoader


class TemporalDataModule(L.LightningDataModule):
    def __init__(
        self,
        *,
        train_representation: PreparedRepresentation,
        validation_representation: PreparedRepresentation,
        seed: int,
        test_representation: PreparedRepresentation | None = None,
        predict_representation: PreparedRepresentation | None = None,
    ) -> None:
        super().__init__()
        self._train_loader = PreparedRepresentationLoader(
            train_representation,
            seed=seed,
            shuffle=True,
        )
        self._validation_loader = PreparedRepresentationLoader(
            validation_representation,
            seed=seed,
            shuffle=False,
        )
        self._test_loader = (
            None
            if test_representation is None
            else PreparedRepresentationLoader(
                test_representation,
                seed=seed,
                shuffle=False,
            )
        )
        self._predict_loader = (
            None
            if predict_representation is None
            else PreparedRepresentationLoader(
                predict_representation,
                seed=seed,
                shuffle=False,
            )
        )

    def train_dataloader(self) -> PreparedRepresentationLoader:
        return self._train_loader

    def val_dataloader(self) -> PreparedRepresentationLoader:
        return self._validation_loader

    def test_dataloader(self) -> PreparedRepresentationLoader:
        if self._test_loader is None:
            raise RuntimeError("test_representation was not configured")
        return self._test_loader

    def predict_dataloader(self) -> PreparedRepresentationLoader:
        if self._predict_loader is None:
            raise RuntimeError("predict_representation was not configured")
        return self._predict_loader
