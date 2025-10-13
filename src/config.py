

# --- Cấu hình Kích thước và Vị trí ---
import os

CONTAINER_WIDTH = 900
CONTAINER_HEIGHT = 500
FORM_WIDTH = CONTAINER_WIDTH // 2
TOGGLE_PANEL_WIDTH = FORM_WIDTH

# --- Cấu hình Thời gian Animation ---
ANIMATION_DURATION_MS = 300

# --- Cấu hình Màu sắc (Hex Codes) ---
COLOR_WHITE = "#FFFFFF"
COLOR_PRIMARY_BLUE = "#5c6bc0"
COLOR_SECONDARY_BLUE = "#2da0a8"
COLOR_PRIMARY_BLUE_PURPLE = "#3f51b5"
COLOR_SECONDARY_BLUE_PURPLE = "#673ab7"
COLOR_GRAY = "#cccccc"
COLOR_SHADOW = "rgba(0, 0, 0, 0.35)"
# --- Resource paths ---
FONT_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'BeVietnamPro-Regular.ttf')

# --- Calendar / Theme colors ---
CALENDAR_BG_GRADIENT_START = "#e6f7ff"
CALENDAR_BG_GRADIENT_END = "#d0f0ff"
CALENDAR_MONTH_PILL_START = "#0277bd"
CALENDAR_MONTH_PILL_END = "#26c6da"

# --- Dialog / Button default colors ---
BTN_PRIMARY_BG = "#007bff"
BTN_PRIMARY_BG_HOVER = "#0056b3"
INPUT_BG = "#f3f3f3"
TEXT_MUTED = "#555555"

# --- UI components in home_page.py ---
# Icon directory (absolute path to assets/icons)
ICON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons'))

COLOR_BACKGROUND = "#F4F6F8"
COLOR_PRIMARY = "#4A90E2"
COLOR_SUCCESS = "#2ECC71"
COLOR_DANGER = "#E74C3C"
COLOR_TEXT_PRIMARY = "#2E3A4B"
COLOR_TEXT_SECONDARY = "#8FA0B3"
COLOR_BORDER = "#EAECEF"
COLOR_HOVER = "#5AA0F2"

# Priority colors mapping used in home_page
PRIORITY_COLORS = {1: "#d1453b", 2: "#09eb32", 3: "#4073d6", 4: "#808080"}