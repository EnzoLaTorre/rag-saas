import time
from collections import defaultdict, deque


class RateLimiter:
    """Limitador de tasa en memoria (ventana deslizante).

    Suficiente para proteger una demo de un solo proceso. En producción con
    varios workers conviene un backend compartido (p. ej. Redis).
    """

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True

    def reset(self) -> None:
        self._hits.clear()
