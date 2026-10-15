"""Spaced repetition: the SM-2 algorithm (Wozniak, 1990), as used by SuperMemo 2 and early Anki (ARCHITECTURE.md 12.2).

After each review the student grades their recall from 0 (blackout) to 5 (perfect). SM-2 keeps three numbers per
card: the easiness factor ef (how fast intervals grow), the current interval in days, and the number of correct
reviews in a row (reps). Cards you know well come back after longer and longer gaps; cards you fail come back
tomorrow.
"""
from __future__ import annotations

MIN_EF = 1.3        # below this, intervals grow too slowly and a hard card is shown almost daily forever
FIRST_INTERVAL = 1  # days after the first correct review
SECOND_INTERVAL = 6  # days after the second correct review in a row
PASS_GRADE = 3      # grades 3-5 are correct recalls; 0-2 are failures


def sm2(ef: float, interval: int, reps: int, grade: int) -> tuple[float, int, int]:
    """One review. Returns the new (ef, interval in days, reps). Raises ValueError for a grade outside 0..5."""
    if not 0 <= grade <= 5:
        raise ValueError(f"grade must be 0..5, got {grade}")
    if grade < PASS_GRADE:
        reps = 0
        interval = FIRST_INTERVAL
    else:
        reps += 1
        if reps == 1:
            interval = FIRST_INTERVAL
        elif reps == 2:
            interval = SECOND_INTERVAL
        else:
            interval = round(interval * ef)
    ef = ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    ef = max(MIN_EF, ef)
    return ef, interval, reps
