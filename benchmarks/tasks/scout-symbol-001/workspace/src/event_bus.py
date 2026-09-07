class EventBus:
    def __init__(self):
        self._handlers = {}

    def on(self, name, callback):
        self._handlers.setdefault(name, []).append(callback)

    def emit(self, name):
        for callback in self._handlers.get(name, []):
            callback()
