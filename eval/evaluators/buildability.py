"""Custom buildability evaluator for LEGO building specifications.

Scores a generated building specification on domain-specific criteria:
dimensions present, valid brick/part references, color palette specified,
structural feasibility, and format compliance.

Returns a score between 0.0 and 1.0 based on how many checks pass.
"""

import re
from typing import Any


# Valid LDraw color codes (subset of commonly used colors).
VALID_LDRAW_COLORS = {
    0, 1, 2, 4, 5, 6, 7, 9, 14, 15, 19, 25, 27, 28, 47, 70, 71, 72,
    84, 150, 212, 272, 288, 308, 320, 334, 378, 462, 484,
}

# Known valid LDraw part numbers (common bricks, plates, slopes, windows, etc.).
VALID_PART_NUMBERS = {
    "3005", "3004", "3622", "3010", "3009", "3008", "3001", "3003",
    "2456", "3002", "6112",  # bricks
    "3024", "3023", "3710", "3666", "3460", "3020", "3795", "3034",
    "3832", "3035", "3028", "3036", "3958", "3031", "4477",  # plates
    "3070b", "3069b", "63864", "2431", "6636", "4162",  # tiles
    "60594", "60592", "60603", "86210", "60596", "57895", "57896",
    "3853", "3856",  # windows/doors
    "3659", "6183", "3307", "3308",  # arches
    "3040b", "3037", "3039", "3038", "85984", "92946", "3665",  # slopes
    "87087", "98283", "15254", "4070", "4073", "2877", "30136",  # specialty
    "3811", "3867",  # baseplates
}

# Known valid part category keywords (for fuzzy matching in natural-language specs).
PART_CATEGORY_KEYWORDS = [
    "brick", "plate", "tile", "slope", "arch", "window", "door",
    "baseplate", "beam", "column", "pillar", "cornice", "bracket",
    "fence", "railing", "stud", "SNOT", "masonry", "grille",
]

# Structural red-flag patterns.
STRUCTURAL_BAD_PATTERNS = [
    r"floating\s+(element|section|floor|wall|roof)",
    r"unsupported\s+(overhang|cantilever|span)",
    r"cantilever.*(?:exceed|over)\s*(?:4|5|6|8|10)\s*studs",
    r"no\s+(?:foundation|base|support)",
]

# Dimension-related patterns (matches phrases like "32 studs wide", "640 LDU", "2-story").
DIMENSION_PATTERNS = [
    r"\d+\s*(?:studs?|LDU)\s*(?:wide|long|tall|deep|high)",
    r"(?:width|depth|height|length)\s*[:=]\s*\d+",
    r"\d+\s*x\s*\d+\s*(?:studs?|baseplate|footprint)",
    r"\d+-?\s*stor(?:y|ies|ey|eys)",
    r"(?:width|depth|height)\s*.*\d+",
]

# Color palette patterns.
COLOR_PALETTE_PATTERNS = [
    r"(?:primary|secondary|accent|trim|roof)\s*(?:color)?\s*[:=]",
    r"(?:color|colour)\s*(?:palette|scheme)",
    r"(?:dark\s+tan|reddish\s+brown|light\s+bluish\s+gray|sand\s+green|white|black|red|blue|yellow|tan|brown|cream|grey|gray)",
    r"color\s+(?:code\s+)?\d+",
]


def _check_dimensions(text: str) -> tuple[bool, str]:
    """Check whether the output includes physical dimensions."""
    for pattern in DIMENSION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, "Dimensions found in output."
    return False, "No physical dimensions (width, depth, height, story count) detected."


def _check_brick_references(text: str) -> tuple[bool, str]:
    """Check whether the output references plausible brick/part names or numbers."""
    # Check for explicit part numbers (e.g., 3004.dat or just 3004).
    part_number_pattern = r"\b(\d{4,5}[a-z]?)(?:\.dat)?\b"
    found_parts = set(re.findall(part_number_pattern, text))
    valid_found = found_parts & VALID_PART_NUMBERS

    if valid_found:
        return True, f"Valid part references found: {', '.join(sorted(valid_found))}."

    # Fall back to category keyword matching.
    text_lower = text.lower()
    matched_keywords = [kw for kw in PART_CATEGORY_KEYWORDS if kw.lower() in text_lower]
    if len(matched_keywords) >= 2:
        return True, f"Part category keywords found: {', '.join(matched_keywords)}."

    return False, "No valid brick/part references or category keywords detected."


def _check_color_palette(text: str) -> tuple[bool, str]:
    """Check whether the output specifies a color palette."""
    for pattern in COLOR_PALETTE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, "Color palette specification found."
    return False, "No color palette or color assignments detected."


def _check_structural_feasibility(text: str) -> tuple[bool, str]:
    """Check for known structural impossibilities in the output."""
    for pattern in STRUCTURAL_BAD_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return False, f"Structural concern detected: '{match.group()}'."
    return True, "No structural red flags detected."


def _check_format_compliance(text: str) -> tuple[bool, str]:
    """Check whether the output follows an expected structured format.

    Looks for section headers or structured key-value layout indicating
    a proper specification rather than freeform prose.
    """
    section_patterns = [
        r"(?:^|\n)\s*#{1,3}\s+",           # Markdown headers
        r"(?:^|\n)\s*\*\*[A-Z]",            # Bold section labels
        r"(?:^|\n)\s*(?:Dimensions|Palette|Features|Construction|Floor\s*Plan|Roof|Walls)\s*[:|-]",
        r"(?:^|\n)\s*-\s+\w+",              # Bullet points
    ]
    matches = sum(1 for p in section_patterns if re.search(p, text, re.IGNORECASE))
    if matches >= 2:
        return True, "Structured format detected (headers/sections/bullets)."
    return False, "Output lacks structured format (no section headers or organized layout)."


def evaluate(response: str, **kwargs: Any) -> dict:
    """Evaluate a single generated building specification for buildability.

    Args:
        response: The generated building specification text to evaluate.
        **kwargs: Additional context (unused, reserved for future checks).

    Returns:
        A dict with:
            - score (float): 0.0 to 1.0 based on fraction of checks passed.
            - details (list[dict]): Per-check results with name, passed, and reason.
    """
    checks = [
        ("dimensions_present", _check_dimensions),
        ("brick_part_references", _check_brick_references),
        ("color_palette_specified", _check_color_palette),
        ("structural_feasibility", _check_structural_feasibility),
        ("format_compliance", _check_format_compliance),
    ]

    details = []
    passed_count = 0

    for name, check_fn in checks:
        passed, reason = check_fn(response)
        details.append({"name": name, "passed": passed, "reason": reason})
        if passed:
            passed_count += 1

    score = passed_count / len(checks) if checks else 0.0

    return {
        "score": round(score, 4),
        "details": details,
    }


if __name__ == "__main__":
    # Quick self-test with a sample specification.
    sample = """
    ## Dimensions
    Width: 32 studs (640 LDU), Depth: 16 studs (320 LDU), Height: 2-story

    ## Color Palette
    Primary color: Dark Tan (28), Secondary: Sand Green (378), Trim: White (15)

    ## Construction
    - Foundation: 3811.dat baseplate 32x32
    - Walls: 3004.dat 1x2 bricks with 98283.dat masonry profile
    - Windows: 60594.dat frames with 60603.dat glass
    - Roof: 3040b.dat slopes forming peaked ridge

    ## Features
    - Ground floor storefront with arched entrance (3659.dat)
    - Upper floor with bay window using bracket supports
    - Dentil cornice band below roofline
    """
    result = evaluate(sample)
    print(f"Score: {result['score']}")
    for detail in result["details"]:
        status = "PASS" if detail["passed"] else "FAIL"
        print(f"  [{status}] {detail['name']}: {detail['reason']}")
