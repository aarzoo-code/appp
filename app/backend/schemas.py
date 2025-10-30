"""
Lightweight helper functions and constants for level math and simple validation.
"""
import math

BASE_XP = 100

def xp_for_level(level: int) -> int:
    """Return total XP required to reach given level (cumulative threshold).
    We'll use a curve: BASE_XP * level ** 1.5
    """
    return int(BASE_XP * (level ** 1.5))

def next_level_threshold(current_level: int) -> int:
    return xp_for_level(current_level + 1)

def compute_new_level(current_xp: int) -> int:
    level = 1
    while True:
        if current_xp < xp_for_level(level + 1):
            return level
        level += 1


def validate_award_payload(payload: dict) -> (bool, str):
    if 'user_id' not in payload:
        return False, 'user_id is required'
    if 'xp' not in payload:
        return False, 'xp is required'
    try:
        xp = int(payload.get('xp', 0))
        if xp <= 0:
            return False, 'xp must be positive'
    except Exception:
        return False, 'xp must be an integer'
    return True, ''
