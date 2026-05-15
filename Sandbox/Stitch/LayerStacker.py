#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional runtime dependency
    np = None


XYZ = Tuple[int, int, int]
XYOffset = Tuple[int, int]


@dataclass(frozen=True)
class StitchedLayer:
    z_index: int
    image: "np.ndarray"
    offset: XYOffset = (0, 0)


class LayerStacker:

    """Align stitched 2D layers in XY and extract a stacked XYZ region."""

    def __init__(self) -> None:
        """Create an empty layer stacker."""
        self.layers: Dict[int, StitchedLayer] = {}

    def add_layer(self, z_index: int, image: "np.ndarray", offset: XYOffset = (0, 0)) -> None:
        self._require_numpy()
        if z_index in self.layers:
            raise ValueError(f"Layer {z_index} is already registered")

        array = np.asarray(image)
        if array.ndim < 2:
            raise ValueError("Layer image must have at least 2 dimensions")

        self.layers[z_index] = StitchedLayer(z_index=z_index, image=array, offset=(int(offset[0]), int(offset[1])))

    def add_layers(self, layers: Mapping[int, "np.ndarray"], offsets: Optional[Mapping[int, XYOffset]] = None) -> None:
        offsets = offsets or {}
        for z_index, image in layers.items():
            self.add_layer(z_index, image, offset=offsets.get(z_index, (0, 0)))

    def stack_region(self, start_xyz: XYZ, end_xyz: XYZ, fill_value: int = 0) -> "np.ndarray":
        """Return an inclusive XYZ crop from the aligned layer set."""
        self._require_numpy()
        if not self.layers:
            raise ValueError("No layers have been registered")

        x_start, y_start, z_start, x_end, y_end, z_end = self._normalize_region(start_xyz, end_xyz)
        first_layer = self._require_layer(z_start)
        slice_shape = (y_end - y_start + 1, x_end - x_start + 1) + first_layer.image.shape[2:]
        volume_shape = (z_end - z_start + 1,) + slice_shape
        volume = np.full(volume_shape, fill_value, dtype=first_layer.image.dtype)

        for output_index, z_index in enumerate(range(z_start, z_end + 1)):
            layer = self._require_layer(z_index)
            volume[output_index] = self._extract_region(layer, x_start, y_start, x_end, y_end, fill_value)

        return volume

    @classmethod
    def from_loader(
        cls,
        loader,
        start_xyz: XYZ,
        end_xyz: XYZ,
        stitch_fn: Callable[[Sequence["np.ndarray"]], "np.ndarray"],
        *,
        offsets: Optional[Mapping[int, XYOffset]] = None,
        tiles=None,
    ) -> "LayerStacker":
        """Build a stacker from a DataLoader-like object plus a stitch function."""
        cls._require_numpy()
        offsets = offsets or {}
        _, _, z_start, _, _, z_end = cls._normalize_region(start_xyz, end_xyz)
        loaded_layers = loader.load(layers=(z_start, z_end), tiles=tiles, load_images=True)

        stacker = cls()
        for z_index, tile_images in loaded_layers.items():
            stitched = stitch_fn(tile_images)
            stacker.add_layer(z_index, stitched, offset=offsets.get(z_index, (0, 0)))

        return stacker

    @classmethod
    def _extract_region(
        cls,
        layer: StitchedLayer,
        x_start: int,
        y_start: int,
        x_end: int,
        y_end: int,
        fill_value: int,
    ) -> "np.ndarray":
        cls._require_numpy()
        height = y_end - y_start + 1
        width = x_end - x_start + 1
        result_shape = (height, width) + layer.image.shape[2:]
        result = np.full(result_shape, fill_value, dtype=layer.image.dtype)

        x_offset, y_offset = layer.offset
        layer_height, layer_width = layer.image.shape[:2]
        layer_x_end = x_offset + layer_width - 1
        layer_y_end = y_offset + layer_height - 1

        overlap_x_start = max(x_start, x_offset)
        overlap_y_start = max(y_start, y_offset)
        overlap_x_end = min(x_end, layer_x_end)
        overlap_y_end = min(y_end, layer_y_end)

        if overlap_x_start > overlap_x_end or overlap_y_start > overlap_y_end:
            return result

        source_x_start = overlap_x_start - x_offset
        source_y_start = overlap_y_start - y_offset
        source_x_end = overlap_x_end - x_offset + 1
        source_y_end = overlap_y_end - y_offset + 1

        target_x_start = overlap_x_start - x_start
        target_y_start = overlap_y_start - y_start
        target_x_end = overlap_x_end - x_start + 1
        target_y_end = overlap_y_end - y_start + 1

        result[target_y_start:target_y_end, target_x_start:target_x_end] = layer.image[
            source_y_start:source_y_end,
            source_x_start:source_x_end,
        ]
        return result

    def _require_layer(self, z_index: int) -> StitchedLayer:
        try:
            return self.layers[z_index]
        except KeyError as exc:
            raise IndexError(f"Layer {z_index} is not available") from exc

    @staticmethod
    def _normalize_region(start_xyz: XYZ, end_xyz: XYZ) -> Tuple[int, int, int, int, int, int]:
        x_start = min(int(start_xyz[0]), int(end_xyz[0]))
        y_start = min(int(start_xyz[1]), int(end_xyz[1]))
        z_start = min(int(start_xyz[2]), int(end_xyz[2]))
        x_end = max(int(start_xyz[0]), int(end_xyz[0]))
        y_end = max(int(start_xyz[1]), int(end_xyz[1]))
        z_end = max(int(start_xyz[2]), int(end_xyz[2]))
        return x_start, y_start, z_start, x_end, y_end, z_end

    @staticmethod
    def _require_numpy() -> None:
        if np is None:
            raise RuntimeError("numpy is required for layer alignment and stacking")
