"""
Convert building spec examples into JSONL format for OpenAI fine-tuning.

Input: JSON file with spec examples
Output: JSONL file with messages arrays

Format:
{"messages": [
  {"role": "system", "content": "You generate LEGO building specs..."},
  {"role": "user", "content": "3-story historic European townhouse"},
  {"role": "assistant", "content": "{\"height\": 3, ...}"}
]}
"""
import argparse
import json
import os

SYSTEM_PROMPT = (
    "You are an expert LEGO building spec generator. Given a description of a "
    "building, produce a detailed JSON specification including: height (floors), "
    "style, facade type, roof type, window pattern, door placement, color palette, "
    "and special features. Output valid JSON only."
)


def convert_to_training_format(specs):
    """Convert a list of spec examples to fine-tuning JSONL format."""
    training_lines = []
    for spec in specs:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": spec["prompt"]},
            {"role": "assistant", "content": json.dumps(spec["spec"], indent=None)},
        ]
        training_lines.append(json.dumps({"messages": messages}))
    return training_lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="../../data/scenario4/spec_examples.json",
                        help="Input JSON file with spec examples")
    parser.add_argument("--output", type=str, default="../../data/scenario4/training_data.jsonl",
                        help="Output JSONL file for fine-tuning")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        # Create sample data if none exists
        sample_specs = [
            {
                "prompt": "3-story historic European townhouse with shop on ground floor",
                "spec": {
                    "height": 3,
                    "style": "historic",
                    "facade": "masonry",
                    "roof": "peaked",
                    "ground_floor": "commercial",
                    "upper_floors": "residential",
                    "windows": {"type": "1x4x3", "per_floor": 3},
                    "door": {"type": "1x4x6", "position": "center"},
                    "colors": {
                        "primary": "dark_tan",
                        "secondary": "sand_green",
                        "accent": "dark_bluish_gray",
                        "trim": "white",
                    },
                    "features": ["cornice", "window_sills", "awning"],
                }
            },
            {
                "prompt": "Modern 2-story office building with glass facade",
                "spec": {
                    "height": 2,
                    "style": "modern",
                    "facade": "smooth",
                    "roof": "flat",
                    "ground_floor": "commercial",
                    "upper_floors": "office",
                    "windows": {"type": "1x4x3", "per_floor": 5},
                    "door": {"type": "1x4x6", "position": "left"},
                    "colors": {
                        "primary": "light_bluish_gray",
                        "secondary": "white",
                        "accent": "black",
                        "trim": "white",
                    },
                    "features": ["rooftop_terrace", "glass_curtain_wall"],
                }
            },
            {
                "prompt": "Small industrial warehouse with roller door",
                "spec": {
                    "height": 1,
                    "style": "industrial",
                    "facade": "corrugated",
                    "roof": "peaked",
                    "ground_floor": "warehouse",
                    "upper_floors": "none",
                    "windows": {"type": "1x2x2", "per_floor": 2},
                    "door": {"type": "roller", "position": "center"},
                    "colors": {
                        "primary": "dark_bluish_gray",
                        "secondary": "light_bluish_gray",
                        "accent": "yellow",
                        "trim": "white",
                    },
                    "features": ["loading_dock", "ventilation"],
                }
            },
        ]
        os.makedirs(os.path.dirname(args.input) or ".", exist_ok=True)
        with open(args.input, "w") as f:
            json.dump(sample_specs, f, indent=2)
        print(f"Created sample spec examples at {args.input}")
        specs = sample_specs
    else:
        with open(args.input) as f:
            specs = json.load(f)

    lines = convert_to_training_format(specs)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {len(lines)} training examples to {args.output}")


if __name__ == "__main__":
    main()
