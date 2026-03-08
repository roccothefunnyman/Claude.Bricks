"""
Extract part-usage statistics from .ldr files.
Produces a CSV with one row per file and numeric feature columns.

Features:
  - total_parts: total number of parts
  - brick_count: bricks (3001, 3002, 3003, 3004, 3005, 3008, 3009, 3010, etc.)
  - plate_count: plates (3020, 3023, 3024, 3034, 3035, 3710, etc.)
  - slope_count: slopes (3037, 3038, 3039, 3040b, 85984, etc.)
  - window_count: windows (60594, 60592, 3853, etc.)
  - door_count: doors (60596, 57895, 57896, etc.)
  - height_studs: building height in studs
  - width_studs: building width in studs
  - depth_studs: building depth in studs
  - window_to_wall_ratio: window_count / total wall parts
"""
import argparse
import csv
import os
from collections import defaultdict

# Part categories
BRICK_PARTS = {"3001", "3002", "3003", "3004", "3005", "3008", "3009", "3010",
               "3622", "2456", "6112", "98283"}
PLATE_PARTS = {"3020", "3023", "3024", "3034", "3035", "3710", "3666", "3460",
               "3795", "3832", "3028", "3036", "3958", "3031", "4477"}
SLOPE_PARTS = {"3037", "3038", "3039", "3040b", "85984", "92946", "3665"}
WINDOW_PARTS = {"60594", "60592", "60603", "86210", "3853", "3856"}
DOOR_PARTS = {"60596", "57895", "57896"}


def extract_stats(filepath):
    """Extract part statistics from a single .ldr file."""
    parts = []
    part_counts = defaultdict(int)

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
                part = tokens[14].replace(".dat", "")
                parts.append((x, y, z, part))
                part_counts[part] += 1
            except (ValueError, IndexError):
                continue

    if not parts:
        return None

    xs = [p[0] for p in parts]
    ys = [p[1] for p in parts]
    zs = [p[2] for p in parts]

    # Dimensions in studs (1 stud = 20 LDU)
    width = (max(xs) - min(xs)) / 20 if xs else 0
    height = (max(ys) - min(ys)) / 24 if ys else 0  # 1 brick = 24 LDU
    depth = (max(zs) - min(zs)) / 20 if zs else 0

    # Categorize parts
    brick_count = sum(part_counts[p] for p in part_counts if p in BRICK_PARTS)
    plate_count = sum(part_counts[p] for p in part_counts if p in PLATE_PARTS)
    slope_count = sum(part_counts[p] for p in part_counts if p in SLOPE_PARTS)
    window_count = sum(part_counts[p] for p in part_counts if p in WINDOW_PARTS)
    door_count = sum(part_counts[p] for p in part_counts if p in DOOR_PARTS)

    wall_parts = brick_count + window_count + door_count
    window_ratio = window_count / wall_parts if wall_parts > 0 else 0

    return {
        "total_parts": len(parts),
        "brick_count": brick_count,
        "plate_count": plate_count,
        "slope_count": slope_count,
        "window_count": window_count,
        "door_count": door_count,
        "height_studs": round(height, 1),
        "width_studs": round(width, 1),
        "depth_studs": round(depth, 1),
        "window_to_wall_ratio": round(window_ratio, 4),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=str, required=True,
                        help="Directory containing .ldr files")
    parser.add_argument("--output-path", type=str, required=True,
                        help="Output CSV file path")
    args = parser.parse_args()

    rows = []
    for fname in sorted(os.listdir(args.input_path)):
        if not fname.lower().endswith(".ldr"):
            continue
        fpath = os.path.join(args.input_path, fname)
        stats = extract_stats(fpath)
        if stats:
            stats["filename"] = fname
            rows.append(stats)

    fieldnames = ["filename", "total_parts", "brick_count", "plate_count",
                  "slope_count", "window_count", "door_count",
                  "height_studs", "width_studs", "depth_studs",
                  "window_to_wall_ratio"]

    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)
    with open(args.output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Extracted stats for {len(rows)} files -> {args.output_path}")


if __name__ == "__main__":
    main()
