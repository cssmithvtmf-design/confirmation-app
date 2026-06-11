"""
CONFIGURATION FILE

All values you will tweak live here.
Only edit this file for positioning and styling.
"""

# =========================
# FILE PATHS
# =========================
BASE_IMAGE = "assets/base_template.png"
#FONT_PATH = "assets/fonts/Rockybilly.ttf"
FONT_PATH = "assets/fonts/Gemstone.ttf"

# =========================
# FONT SETTINGS
# =========================

# Your chosen size (nice choice for this template)
FONT_SIZE = 59

# Slightly softened dark gray (blends better than black)
TEXT_COLOR = (55, 55, 55)

# Shadow layers (for depth)
SHADOW_DARK = (0, 0, 0)
SHADOW_LIGHT = (80, 80, 80)

# Shadow offsets (tweak to change depth feel)
SHADOW_OFFSET_PRIMARY = (2, 2)
SHADOW_OFFSET_SECONDARY = (1, 1)


# =========================
# POSITIONING
# =========================

"""
X position where text begins.

Adjust this if:
- text is too far right -> lower number
- text is too far left -> higher number
"""
TEXT_START_X = 420


"""
Y positions = ACTUAL LINE (baseline reference)

These are tuned to YOUR image already.
Only adjust if something is slightly off visually.
"""
LINE_Y = {
    "client": 1097,
    "date":   1230,
    "time":   1352,
    "price":  1468,
}


"""
BASELINE OFFSET (VERY IMPORTANT)

This controls how text sits on the line.

Increase = moves text DOWN  
Decrease = moves text UP  

This is the KEY tuning control now.
"""
BASELINE_OFFSET = 14


# =========================
# OUTPUT SETTINGS
# =========================
OUTPUT_DIR = "output"