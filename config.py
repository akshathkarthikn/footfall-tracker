"""
Application configuration for Footfall Tracker.
"""

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Application settings
APP_NAME = "Footfall Tracker"
APP_VERSION = "1.0.0"

# Default operating hours (can be overridden in settings)
DEFAULT_OPENING_HOUR = 9
DEFAULT_CLOSING_HOUR = 21

# Validation limits
MIN_FOOTFALL_VALUE = 0
MAX_FOOTFALL_VALUE = 10000  # Can be overridden in settings

# Spike detection
DEFAULT_SPIKE_THRESHOLD_PERCENT = 50  # Warn if value > previous * 1.5

# Edit window for entry users (hours)
DEFAULT_EDIT_WINDOW_HOURS = 2

# Auto-refresh interval for dashboard (seconds)
DASHBOARD_REFRESH_INTERVAL = 300  # 5 minutes

# Chart colors
CHART_COLORS = [
    '#EA580C',  # Orange
    '#2563EB',  # Blue
    '#16A34A',  # Green
    '#DC2626',  # Red
    '#7C3AED',  # Purple
    '#0891B2',  # Cyan
    '#CA8A04',  # Yellow
    '#BE185D',  # Pink
]

# Floor colors for consistency across charts
def get_floor_color(index: int) -> str:
    """Get a consistent color for a floor by index."""
    return CHART_COLORS[index % len(CHART_COLORS)]
