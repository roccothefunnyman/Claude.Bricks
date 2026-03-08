"""
Parse .ldr files and extract numeric features for anomaly detection.
Outputs a CSV with one row per file and four features plus a label column.

Features:
  - overhang_ratio: unsupported parts / total parts
  - collision_count: overlapping brick positions
  - height_to_base_ratio: height range / footprint area
  - layer_density: variance of parts-per-layer distribution
"""
import argparse
import csv
import os
import re
from collections import defaultdict


def parse_ldr_parts(filepath):
    """Parse type-1 lines from an .ldr file, return list of (x, y, z, part)."""
    parts = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("1 "):
                continue
            tokens = line.split()
            if len(tokens) < 15:
                continue
            try:
                x = float(tokens[2])
                y = float(tokens[3])
                z = float(tokens[4])
                part = tokens[14]
                parts.append((x, y, z, part))
            except (ValueError, IndexError):
                continue
    return parts


def compute_features(parts):
    """Compute the four features from parsed parts."""
    if not parts:
        return 0.0, 0, 0.0, 0.0

    xs = [p[0] for p in parts]
    ys = [p[1] for p in parts]
    zs = [p[2] for p in parts]

    # Height-to-base ratio
    x_range = max(xs) - min(xs) if xs else 1
    z_range = max(zs) - min(zs) if zs else 1
    y_range = max(ys) - min(ys) if ys else 1
    footprint = max(x_range * z_range, 1)
    height_to_base = y_range / (footprint ** 0.5)

    # Layer density (variance of parts per Y layer)
    layers = defaultdict(int)
    for _, y, _, _ in parts:
        layers[round(y)] += 1
    counts = list(layers.values())
    mean_count = sum(counts) / len(counts) if counts else 0
    variance = sum((c - mean_count) ** 2 for c in counts) / len(counts) if counts else 0

    # Collision count (parts at exact same position)
    positions = [(round(p[0], 1), round(p[1], 1), round(p[2], 1)) for p in parts]
    collision_count = len(positions) - len(set(positions))

    # Overhang ratio (parts with no support directly below)
    y_positions = defaultdict(set)
    for x, y, z, _ in parts:
        y_positions[round(y)].add((round(x, 1), round(z, 1)))

    sorted_layers = sorted(y_positions.keys())
    unsupported = 0
    for i, y_layer in enumerate(sorted_layers):
        if i == 0:
            continue
        layer_below = sorted_layers[i - 1]
        below_positions = set(y_positions.get(layer_below, []))
        for pos in y_positions[y_layer]:
            if pos not in below_positions:
                unsupported += 1
    total = len(parts)
    overhang_ratio = unsupported / total if total > 0 else 0

    return overhang_ratio, collision_count, height_to_base, variance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=str, required=True,
                        help="Directory containing .ldr files")
    parser.add_argument("--output-path", type=str, required=True,
                        help="Output CSV file path")
    parser.add_argument("--label-file", type=str, default=None,
                        help="Optional CSV with filename,label columns")
    args = parser.parse_args()

    # Load labels if provided
    labels = {}
    if args.label_file and os.path.exists(args.label_file):
        with open(args.label_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                labels[row["filename"]] = int(row["label"])

    # Process all .ldr files
    rows = []
    for fname in sorted(os.listdir(args.input_path)):
        if not fname.lower().endswith(".ldr"):
            continue
        fpath = os.path.join(args.input_path, fname)
        parts = parse_ldr_parts(fpath)
        overhang, collisions, htb, density = compute_features(parts)
        label = labels.get(fname, 0)
        rows.append({
            "filename": fname,
            "overhang_ratio": round(overhang, 4),
            "collision_count": collisions,
            "height_to_base_ratio": round(htb, 4),
            "layer_density": round(density, 4),
            "label": label,
        })

    # Write CSV
    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)
    with open(args.output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "overhang_ratio", "collision_count",
            "height_to_base_ratio", "layer_density", "label"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Extracted features for {len(rows)} files -> {args.output_path}")


if __name__ == "__main__":
    main()
