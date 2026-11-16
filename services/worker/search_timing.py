"""Content-free timing for one search request."""
from contextlib import contextmanager
from time import monotonic


class SearchTiming:
    def __init__(self):
        self.started = monotonic()
        self.times = {}
        self.cache = 'skipped'

    def call(self, stage, operation, *args, **kwargs):
        with self.measure(stage):
            return operation(*args, **kwargs)

    @contextmanager
    def measure(self, stage):
        start = monotonic()
        try:
            yield
        finally:
            self.times[stage] = self.times.get(stage, 0) + (monotonic()-start)

    def receipt(self, *, succeeded, compact):
        return {'outcome': 'ok' if succeeded else 'failed',
                'route': 'previews' if compact else 'legacy', 'cache': self.cache,
                'total_ms': round((monotonic()-self.started)*1000, 1),
                'stages_ms': {stage: round(seconds*1000, 1) for stage, seconds in self.times.items()}}


def timed(timing, stage, operation, *args, **kwargs):
    if timing is None:
        return operation(*args, **kwargs)
    return timing.call(stage, operation, *args, **kwargs)
