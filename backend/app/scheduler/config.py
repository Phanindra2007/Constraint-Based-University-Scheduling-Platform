"""Fixed scheduler configuration for the current version.

These values can be made configurable in a later version.
"""

from datetime import time

NUM_DAYS = 2
NUM_PERIODS = 6
PERIOD_DURATION_MINUTES = 60
MIN_PREFERENCE_SCORE = 0
MAX_PREFERENCE_SCORE = 10

TEACHING_BLOCKS = [
    [0, 1, 2],
    [3, 4, 5],
]

# Each entry is the clock-time start of the corresponding teaching block.
TEACHING_BLOCK_START_TIMES = [
    time(9, 0),
    time(13, 0),
]

# Internal marker for a course that accepts any room type.
ANY_ROOM_TYPE = "*"
