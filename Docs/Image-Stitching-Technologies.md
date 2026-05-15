<!-- markdownlint-disable MD013 MD034 MD043 -->

# Image Stitching Technologies

This note captures a short list of image-stitching technologies that are relevant to STS and can be shared with Randal as a starting point for tool selection.

## Current Repository Context

The current sandbox already leans toward ImageJ/Fiji from Python:

- `Sandbox/Stitch/stitching.py` initializes `imagej` and calls Fiji's `Grid/Collection stitching` plugin.
- `Sandbox/Stitch/layermerge.py` also uses ImageJ from Python for follow-on image processing.

That makes Fiji-compatible tooling the lowest-friction baseline for STS today.

## Shortlist

| Technology | Strengths | Risks / Limits | Fit For STS |
| --- | --- | --- | --- |
| Fiji `Grid/Collection Stitching` | Purpose-built for tiled microscopy images, supports metadata-driven layouts, virtual memory, and downsampling for large jobs | More of a plugin workflow than a fully custom software library | Best near-term baseline because it already matches the current sandbox direction |
| BigStitcher | Built for large tiled and multi-view microscopy datasets, supports irregular grids, global optimization, fusion, and headless workflows | Heavier workflow and more setup than the simpler Fiji stitching plugin | Best upgrade path once STS needs larger 3D datasets and more robust global alignment |
| TrakEM2 | Includes image registration, stitching, 3D modeling, and annotation in one ImageJ ecosystem tool | Older and broader than a pure stitching pipeline, so it is not the cleanest automation target | Useful as a reference or fallback for manual curation and reconstruction-heavy workflows |
| OpenCV stitching module | Flexible low-level C++/Python integration for custom pipelines and downstream processing | Documentation and defaults are more general-purpose than microscopy-specific | Good if STS eventually needs a fully custom programmable pipeline rather than a Fiji-first workflow |

## Recommended Direction

1. Keep Fiji `Grid/Collection Stitching` as the immediate baseline.
2. Use PyImageJ as the Python bridge so STS can script Fiji/ImageJ functionality inside a larger Python pipeline.
3. Evaluate BigStitcher next if the dataset size, irregular tiling, or 3D reconstruction workload outgrows the simpler plugin flow.
4. Keep OpenCV as the custom-pipeline fallback when STS needs tighter control over stitching internals or integration with other computer-vision steps.

## What To Share With Randal

- The fastest path is to keep building on Fiji/ImageJ because the repo already uses it.
- BigStitcher is the strongest candidate when STS moves from simple tiled stitching to large-scale 3D alignment and fusion.
- OpenCV is viable, but it is better treated as a lower-level engineering option than as the first microscopy-oriented tool choice.

## Sources

- ImageJ Grid/Collection Stitching Plugin: https://imagej.net/plugins/grid-collection-stitching
- BigStitcher documentation: https://imagej.net/plugins/bigstitcher/
- TrakEM2 documentation: https://imagej.net/plugins/trakem2/
- OpenCV stitching module docs: https://docs.opencv.org/4.x/d1/d46/group__stitching.html
- PyImageJ documentation: https://py.imagej.net/en/latest/
