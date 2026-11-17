"""Shared test doubles."""


class SyncThread:
    """Stands in for threading.Thread so background work runs immediately and tests stay deterministic."""
    def __init__(self, target, args=(), **_kwargs):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)
