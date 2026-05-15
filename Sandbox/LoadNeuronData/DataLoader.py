#!/usr/bin/env python3

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Dict, Iterable, List, Optional, Sequence, Tuple, Union

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional runtime dependency
    np = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional runtime dependency
    Image = None


RangeSpec = Optional[Union[int, Sequence[int]]]
ImageValue = Union["np.ndarray", Path]


@dataclass(frozen=True)
class LayerRecord:
    identifier: int
    path: Path
    tiles: Tuple[Path, ...]


class DataLoader:  # noqa: D203,D213
    """Load sequential FlyEM layers and tiles from a directory tree.

    The loader scans the dataset once per root path and caches the discovered
    layer/tile structure at the class level so repeated instances do not need
    to rescan the dataset.
    """

    IMAGE_SUFFIXES: ClassVar[Tuple[str, ...]] = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")
    _DATASET_CACHE: ClassVar[Dict[Path, Tuple[LayerRecord, ...]]] = {}

    def __init__(self, root: Union[str, Path]) -> None:
        """Create a loader for a FlyEM layer/tile dataset root."""
        self.root = Path(root).expanduser().resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"Dataset root does not exist: {self.root}")
        if not self.root.is_dir():
            raise NotADirectoryError(f"Dataset root is not a directory: {self.root}")

        if self.root not in self._DATASET_CACHE:
            self._DATASET_CACHE[self.root] = self._scan_dataset(self.root)

        self.layers = self._DATASET_CACHE[self.root]
        self.layer_ids = [layer.identifier for layer in self.layers]
        self._layers_by_id = {layer.identifier: layer for layer in self.layers}

    def get_layer_count(self) -> int:
        return len(self.layers)

    def get_layer_ids(self) -> List[int]:
        return list(self.layer_ids)

    def get_tile_count(self, layer_id: int) -> int:
        return len(self._require_layer(layer_id).tiles)

    def get_tile_counts(self) -> Dict[int, int]:
        return {layer.identifier: len(layer.tiles) for layer in self.layers}

    def load(
        self,
        layers: RangeSpec = None,
        tiles: RangeSpec = None,
        *,
        load_images: bool = True,
    ) -> Dict[int, List[ImageValue]]:  # noqa: D213
        """Return a sequential layer->tiles dictionary.

        `layers` may be:
        - `None` to load every layer
        - an `int` to load a single layer
        - a `(start, end)` pair to load an inclusive range of layer IDs

        `tiles` may be:
        - `None` to load every tile from each requested layer
        - an `int` to load a single tile index from each layer
        - a `(start, end)` pair to load an inclusive range of tile indices
        """
        layer_ids = self._resolve_layer_ids(layers)
        loaded: Dict[int, List[ImageValue]] = {}

        for layer_id in layer_ids:
            layer = self._require_layer(layer_id)
            tile_indices = self._resolve_tile_indices(layer, tiles)
            loaded[layer_id] = [self._load_tile(layer.tiles[index], load_images=load_images) for index in tile_indices]

        return loaded

    def load_paths(self, layers: RangeSpec = None, tiles: RangeSpec = None) -> Dict[int, List[Path]]:
        return self.load(layers=layers, tiles=tiles, load_images=False)  # type: ignore[return-value]

    def _require_layer(self, layer_id: int) -> LayerRecord:
        try:
            return self._layers_by_id[layer_id]
        except KeyError as exc:
            raise IndexError(f"Layer {layer_id} does not exist") from exc

    def _resolve_layer_ids(self, layers: RangeSpec) -> List[int]:
        if layers is None:
            return list(self.layer_ids)

        if isinstance(layers, int):
            self._require_layer(layers)
            return [layers]

        start, end = self._parse_range(layers, "layers")
        resolved = [layer_id for layer_id in self.layer_ids if start <= layer_id <= end]
        expected = list(range(start, end + 1))
        if resolved != expected:
            missing = [layer_id for layer_id in expected if layer_id not in self._layers_by_id]
            raise IndexError(f"Requested layer range contains missing layers: {missing}")
        return resolved

    def _resolve_tile_indices(self, layer: LayerRecord, tiles: RangeSpec) -> List[int]:
        if tiles is None:
            return list(range(len(layer.tiles)))

        if isinstance(tiles, int):
            self._validate_tile_index(layer, tiles)
            return [tiles]

        start, end = self._parse_range(tiles, "tiles")
        for tile_index in range(start, end + 1):
            self._validate_tile_index(layer, tile_index)
        return list(range(start, end + 1))

    @staticmethod
    def _parse_range(value: Sequence[int], label: str) -> Tuple[int, int]:
        if len(value) == 1:
            start = int(value[0])
            end = start
        elif len(value) == 2:
            start = int(value[0])
            end = start if value[1] is None else int(value[1])
        else:
            raise ValueError(f"{label} must be an int, None, or a 1-item or 2-item range")
        if start < 0 or end < 0:
            raise IndexError(f"{label} indices must be non-negative")
        if end < start:
            raise ValueError(f"{label} range must be ordered as (start, end)")
        return start, end

    @staticmethod
    def _validate_tile_index(layer: LayerRecord, tile_index: int) -> None:
        if tile_index < 0 or tile_index >= len(layer.tiles):
            raise IndexError(f"Tile {tile_index} does not exist in layer {layer.identifier}")

    @staticmethod
    def _load_tile(tile_path: Path, *, load_images: bool) -> ImageValue:
        if not load_images:
            return tile_path

        if Image is None or np is None:
            raise RuntimeError("Pillow and numpy are required to load images into memory")

        with Image.open(tile_path) as image:
            return np.asarray(image)

    @classmethod
    def _scan_dataset(cls, root: Path) -> Tuple[LayerRecord, ...]:
        layer_dirs = [entry for entry in root.iterdir() if entry.is_dir()]
        records: List[LayerRecord] = []

        for fallback_id, layer_dir in enumerate(sorted(layer_dirs, key=lambda item: cls._natural_sort_key(item.name))):
            image_files = tuple(sorted(cls._iter_image_files(layer_dir), key=lambda item: cls._natural_sort_key(str(item.relative_to(layer_dir)))))
            if not image_files:
                continue
            records.append(
                LayerRecord(
                    identifier=cls._extract_identifier(layer_dir.name, fallback_id),
                    path=layer_dir,
                    tiles=image_files,
                )
            )

        if records:
            identifiers = [record.identifier for record in records]
            if len(set(identifiers)) != len(identifiers):
                raise ValueError(f"Layer identifiers must be unique, found duplicates in dataset root: {root}")
            return tuple(sorted(records, key=lambda layer: layer.identifier))

        root_images = tuple(sorted(cls._iter_image_files(root), key=lambda item: cls._natural_sort_key(str(item.relative_to(root)))))
        if root_images:
            return (LayerRecord(identifier=0, path=root, tiles=root_images),)

        raise FileNotFoundError(f"No image files were found under dataset root: {root}")

    @classmethod
    def _iter_image_files(cls, directory: Path) -> Iterable[Path]:
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in cls.IMAGE_SUFFIXES:
                yield path

    @staticmethod
    def _extract_identifier(name: str, fallback: int) -> int:
        match = re.search(r"\d+", name)
        return int(match.group(0)) if match else fallback

    @staticmethod
    def _natural_sort_key(value: str) -> Tuple[Union[int, str], ...]:
        parts = re.split(r"(\d+)", value.lower())
        return tuple(int(part) if part.isdigit() else part for part in parts if part)
