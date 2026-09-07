class DeviceService:
    def __init__(self, events):
        self.events = events

    def flash(self, programmer):
        ok = programmer.program()
        if ok:
            self.events.emit("flash_completed")
        return ok
