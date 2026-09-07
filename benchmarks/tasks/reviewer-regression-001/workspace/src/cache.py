def is_expired(created_at: float, now: float, ttl: float) -> bool:
    age = now - created_at
    return age < ttl
