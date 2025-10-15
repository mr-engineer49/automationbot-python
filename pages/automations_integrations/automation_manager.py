# core/automation_manager.py
import threading
import time

class N8nAutomationScheduler:
    def __init__(self, connector, interval=300):
        self.connector = connector
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            print("[Scheduler] Checking workflows...")
            # You could fetch and run automatically based on rules
            workflows = self.connector.get_workflows()
            for wf in workflows.get("data", []):
                if wf.get("active", False):
                    print(f"Auto-running active workflow: {wf['name']}")
                    self.connector.run_workflow(wf["id"])
            time.sleep(self.interval)
