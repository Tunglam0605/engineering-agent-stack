class MainWindow:
    def __init__(self, service):
        self.service = service
        self.metadata = {}
        self.service.events.on("flash_completed", self.refresh_metadata)

    def refresh_metadata(self):
        self.metadata = {"status": "fresh"}
