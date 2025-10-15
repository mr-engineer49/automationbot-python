import threading
import time

class WorkflowScheduler:
    def __init__(self):
        self.jobs = {}
        self.running = True

    def add_job(self, name, interval, function):
        def job_runner():
            while self.running:
                try:
                    function()
                except Exception as e:
                    print(f"Error in {name}: {e}")
                time.sleep(interval)
        t = threading.Thread(target=job_runner, daemon=True)
        t.start()
        self.jobs[name] = t

    def stop_all(self):
        self.running = False
