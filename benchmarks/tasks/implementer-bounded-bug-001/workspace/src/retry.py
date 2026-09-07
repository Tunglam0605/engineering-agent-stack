def backoff_delay(attempt: int, base: float = 0.1, cap: float = 5.0) -> float:
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    return min(cap, base * (2 ** attempt))
