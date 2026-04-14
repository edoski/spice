"""Shared discovery backbone for SPICE architectural seams."""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import entry_points
from typing import Generic, TypeVar

from .errors import ConfigResolutionError

T = TypeVar("T")


class ComponentCatalog(Generic[T]):
    """Generic discovery catalog shared by SPICE plugin-like architectural seams."""

    def __init__(
        self,
        *,
        kind_label: str,
        entry_point_group: str | None = None,
    ) -> None:
        self.kind_label = kind_label
        self.entry_point_group = entry_point_group
        self._components: dict[str, T] = {}
        self._builtin_loader: Callable[[], None] | None = None
        self._builtins_loaded = False
        self._entry_points_loaded = False

    def configure_builtin_loader(self, loader: Callable[[], None]) -> None:
        """Register the one-shot builtin loader for this seam."""

        self._builtin_loader = loader

    def register(self, component_id: str, component: T) -> None:
        """Register one builtin or discovered component by stable short id."""

        existing = self._components.get(component_id)
        if existing is not None:
            raise ValueError(f"Duplicate {self.kind_label} id: {component_id}")
        self._components[component_id] = component

    def get(self, component_id: str) -> T:
        """Resolve one component after builtin and optional entry-point discovery."""

        self._ensure_loaded()
        try:
            return self._components[component_id]
        except KeyError as exc:
            known = ", ".join(sorted(self._components)) or "<none>"
            raise ConfigResolutionError(
                f"Unknown {self.kind_label}: {component_id}. Known {self.kind_label}s: {known}"
            ) from exc

    def known_ids(self) -> tuple[str, ...]:
        """List discovered ids for operator-facing error reporting and inspection."""

        self._ensure_loaded()
        return tuple(sorted(self._components))

    def _ensure_loaded(self) -> None:
        self._ensure_builtins_loaded()
        self._ensure_entry_points_loaded()

    def _ensure_builtins_loaded(self) -> None:
        if self._builtins_loaded or self._builtin_loader is None:
            return
        self._builtins_loaded = True
        self._builtin_loader()

    def _ensure_entry_points_loaded(self) -> None:
        if self._entry_points_loaded or self.entry_point_group is None:
            return
        self._entry_points_loaded = True
        for entry_point in entry_points(group=self.entry_point_group):
            loaded = entry_point.load()
            self.register(entry_point.name, loaded)
