# STS Work Division Plan

This note translates the current architecture and milestone work into a reviewable project structure and a first-pass work split.

## Purpose

- define how STS work should be divided after the class/module boundaries are known
- map each work area onto a clear repository location
- make issue-sized assignments easier to create from the existing work-item templates

## Proposed Work Areas

| Work Area | Responsibility | Current or Target Location |
| --- | --- | --- |
| Dataset loading | enumerate layers and tiles, validate dataset ranges, expose ordered reads | `Sandbox/LoadNeuronData/`, future `Source/Core/Loader/...` |
| Tile stitching | combine overlapping tiles within a layer | `Sandbox/Stitch/stitching.py`, future stitching backend module |
| Layer stacking | align stitched layers and build XYZ sub-volumes | `Sandbox/Stitch/LayerStacker.py`, future volume assembly module |
| Feature extraction | compute neuron-relevant measurements and derived geometry | `Source/Core/NeuronFeatureExtraction/...` |
| Shared structures | system-wide data structures and stable cross-module interfaces | `Source/Core/Structures/...` |
| Utilities | config loading, logging, and other non-domain helpers | `Source/Core/Utils/...` |

## Suggested Implementation Sequence

1. Stabilize the data loader API.
2. Stabilize the stitching interface so it accepts ordered tiles and returns a stitched layer.
3. Stabilize the layer-stacking API for XYZ requests.
4. Define the volume handoff shape used by feature extraction.
5. Split feature extraction tasks into smaller algorithm-specific work items.

## Suggested Work Split

| Work Item | Owner Type | Depends On |
| --- | --- | --- |
| loader cleanup and test coverage | data-loading contributor | dataset format assumptions |
| stitching backend experiments | image-processing contributor | loader output shape |
| stacker and volume request interfaces | image-processing contributor | stitched-layer format |
| feature extraction prototypes | analysis contributor | stable volume handoff |
| shared structures and config cleanup | infrastructure contributor | agreed module boundaries |
| integration into NES/ERS handoff | systems contributor | feature extraction outputs |

## Repo Structure Direction

The current repo already contains the beginning of a long-term structure under `Source/Core`. The next step should be to mirror the milestone boundaries there rather than keeping new logic only in sandbox scripts.

Suggested direction:

- keep experimentation in `Sandbox/` until interfaces settle
- promote stable loader code into `Source/Core/Loader/`
- promote stable stacking or volume request structures into `Source/Core/Structures/`
- keep analysis algorithms under `Source/Core/NeuronFeatureExtraction/`
- keep configuration and logging under `Source/Core/Utils/`

## Turning This Into Assignments

Use `Docs/Templates/WorkItem-Assignment.md` for each work area above.

Recommended first assignment subjects:

- implement or harden the loader interface
- define the stitched-layer output contract
- define the requested-volume input contract
- isolate one feature-extraction algorithm behind a stable input/output shape

## Notes

- This document is intentionally a planning artifact rather than a code template drop.
- Once the interfaces above are accepted, the follow-on step is to create class or package templates for each work area with one PR per module boundary.
