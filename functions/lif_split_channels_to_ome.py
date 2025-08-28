#!/usr/bin/env python3
"""
lif_split_channels_to_ome.py

Extract all scenes from a Leica .lif and save per-channel Z-stacks as OME-TIFF.
- Keeps Z as a stack (dim order ZYX).
- If multiple timepoints exist, writes one file per T per channel.
- Works both as an importable module (call split_lif_to_channels) and as a CLI.

Requirements:
    pip install bioio bioio-lif bioio-ome-tiff numpy
"""

from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
from bioio import BioImage
from bioio_ome_tiff.writers import OmeTiffWriter
import bioio_lif  # if you want to force the LIF reader, uncomment and pass reader=bioio_lif.Reader


def _safe(name: str) -> str:
    """Make a filesystem-safe name."""
    name = re.sub(r"[^\w\-.]+", "_", str(name))
    return name.strip("_") or "unnamed"

def _dim_labels(dims) -> list[str]:
    """
    Return a list of dimension labels in order (e.g., ['T','C','Z','Y','X'])
    from either a string like 'TCZYX' or a bioio Dimensions object.
    """
    order = getattr(dims, "order", dims)  # Dimensions.order -> 'TCZYX'
    if isinstance(order, str):
        return list(order)
    return list(str(order))

def _normalize_cli_names(arg_list: Optional[list[str]]) -> Optional[list[str]]:
    """
    Accepts:
      - ['DAPI','GFP','RFP']  (space-separated)
      - ['DAPI,GFP,RFP']      (single comma-separated argument)
    Returns a clean list or None.
    """
    if not arg_list:
        return None
    if len(arg_list) == 1 and ("," in arg_list[0]):
        return [s.strip() for s in arg_list[0].split(",") if s.strip()]
    return [s.strip() for s in arg_list if s.strip()]


def split_lif_to_channels(
    lif_path: str | Path,
    outdir: Optional[str | Path] = None,
    *,
    bigtiff: bool = False,
    dtype: str = "native",  # one of {"native","uint16","uint8","float32"}
    include_empty: bool = False,
    verbose: bool = True,
    channel_names: Optional[Iterable[str]] = None,  # <-- NEW
) -> List[Path]:
    """
    Convert a Leica .lif into per-channel OME-TIFF Z-stacks for every scene.

    Parameters
    ----------
    lif_path : str | Path
        Input .lif file.
    outdir : str | Path | None
        Output directory (default: "<lif_basename>_export" next to the input).
    bigtiff : bool
        Force BigTIFF writing.
    dtype : str
        Optional cast before writing. One of: "native", "uint16", "uint8", "float32".
    include_empty : bool
        Keep scenes with zero-sized Z or C (usually skipped).
    verbose : bool
        Print progress.
    channel_names : Iterable[str] | None
        Custom names to apply to channels for **all scenes**. If provided and the
        list is shorter than the number of channels in a scene, the remaining
        channels are named by index; if longer, extras are ignored (with a note).

    Returns
    -------
    List[Path]
        Paths of all written OME-TIFF files.
    """
    lif_path = Path(lif_path)
    if not lif_path.exists():
        raise FileNotFoundError(f"Input not found: {lif_path}")

    outdir = Path(outdir) if outdir is not None else lif_path.with_suffix("").parent / f"{lif_path.stem}_export"
    outdir.mkdir(parents=True, exist_ok=True)

    # Load via BioIO (auto-detects the LIF reader when bioio-lif is installed)
    img = BioImage(str(lif_path), reader = bioio_lif.Reader)

    def _log(msg: str) -> None:
        if verbose:
            print(msg)

    written: List[Path] = []

    # Try channel names from metadata (may be None)
    try:
        base_channel_names = list(img.channel_names) if img.channel_names is not None else None
    except Exception:
        base_channel_names = None

    # User-supplied override (if any)
    override_names = list(channel_names) if channel_names else None

    _log(f"Opened: {lif_path}")
    _log(f"Scenes: {len(img.scenes)}  Dims: {''.join(_dim_labels(img.dims))}  Shape: {img.dask_data.shape}")
    if base_channel_names:
        _log(f"Channel names (first scene): {base_channel_names}")
    if override_names:
        _log(f"Custom channel names override: {override_names}")

    # dtype map
    dtype_map = {"uint16": np.uint16, "uint8": np.uint8, "float32": np.float32}
    if dtype != "native" and dtype not in dtype_map:
        raise ValueError(f"Unsupported dtype '{dtype}'. Choose one of: native, {', '.join(dtype_map.keys())}")

    for scene in img.scenes:
        img.set_scene(scene)
        scene_dir = outdir / f"scene_{_safe(scene)}"
        scene_dir.mkdir(parents=True, exist_ok=True)

        # Per-scene shapes/sizes (scenes can differ!)
        dims = img.dims
        shape = img.dask_data.shape
        labels = _dim_labels(dims)
        size_map = dict(zip(labels, shape))
        nT = size_map.get("T", 1)
        nC = size_map.get("C", 1)
        nZ = size_map.get("Z", 1)

        # Per-scene metadata channel names (fallback if no override provided)
        try:
            scene_channel_names = list(img.channel_names) if img.channel_names is not None else base_channel_names
        except Exception:
            scene_channel_names = base_channel_names

        if (nC == 0 or nZ == 0) and not include_empty:
            _log(f"Skipping empty scene '{scene}' (C={nC}, Z={nZ})")
            continue

        _log(f"- Scene '{scene}': dims={''.join(labels)}, shape={shape} -> T={nT}, C={nC}, Z={nZ}")
        if override_names and len(override_names) != nC:
            _log(f"  Note: Provided {len(override_names)} custom names for C={nC}; "
                 f"extras will be ignored or missing ones filled with indices.")

        # Resolve the names we will use for this scene
        if override_names:
            scene_names = [override_names[i] if i < len(override_names) else None for i in range(nC)]
        else:
            scene_names = scene_channel_names if scene_channel_names else [None] * nC

        _log(f"Scenes: {len(img.scenes)}  Dims: {''.join(_dim_labels(img.dims))}  Shape: {img.dask_data.shape}")

        for t in range(nT):
            for c in range(nC):
                # Pull out a single channel ZYX stack at time t (if T exists)
                if "T" in labels:
                    zyx = img.get_image_data("ZYX", T=t, C=c)
                else:
                    zyx = img.get_image_data("ZYX", C=c)

                # Optional dtype cast
                if dtype != "native":
                    zyx = zyx.astype(dtype_map[dtype], copy=False)

                # Channel name (safe)
                if scene_names and scene_names[c]:
                    ch_part = f"_ch-{_safe(scene_names[c])}"
                else:
                    ch_part = f"_c{c:02d}"

                fname = f"{lif_path.stem}_scene-{_safe(scene)}{ch_part}.ome.tif"
                out_path = scene_dir / fname

                OmeTiffWriter.save(
                    zyx,
                    uri=str(out_path),
                    dim_order="ZYX",
                    bigtiff=bigtiff,
                )

                written.append(out_path)
                _log(f"  Saved: {out_path}")

    _log(f"\nDone. Wrote {len(written)} file(s) to: {outdir}")
    return written


# -------------------- CLI wrapper -------------------- #

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Extract all scenes from a Leica .lif and save per-channel Z-stacks as OME-TIFF."
    )
    p.add_argument("lif_path", type=Path, help="Path to input .lif file")
    p.add_argument("-o", "--outdir", type=Path, default=None, help="Output directory (default: <lif_basename>_export)")
    p.add_argument("--bigtiff", action="store_true", help="Force BigTIFF writing")
    p.add_argument(
        "--dtype",
        choices=["native", "uint16", "uint8", "float32"],
        default="native",
        help="Optional cast before writing (default: native)",
    )
    p.add_argument("--include-empty", action="store_true", help="Keep scenes with zero-sized Z or C (debugging)")
    p.add_argument("--quiet", action="store_true", help="Reduce logging")
    # NEW: custom names
    p.add_argument(
        "-n", "--channel-names",
        nargs="+",
        help='Custom channel names for all scenes, e.g. -n DAPI GFP RFP or -n "DAPI,GFP,RFP"',
    )
    return p


def main(argv: Optional[Iterable[str]] = None) -> None:
    p = _build_argparser()
    args = p.parse_args(argv)
    split_lif_to_channels(
        lif_path=args.lif_path,
        outdir=args.outdir,
        bigtiff=args.bigtiff,
        dtype=args.dtype,
        include_empty=args.include_empty,
        verbose=not args.quiet,
        channel_names=_normalize_cli_names(args.channel_names),  # <-- NEW
    )


if __name__ == "__main__":
    main()