__author__ = 'pbelon'
import sched
import time
import threading
import os
import signal

# TODO: Implement a mechanism for process staying alive longer than its schedule.
class SchedManager:
    scheduler = None
    scheduler_thread = None

    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)

    # Used to run the module immediately.
    def run_now(self, run_method):
        run_method()

    # Used to tell the schedule manager what time to run your module.
    # Parameters[ Datetime: run_time, function: run_method]
    def run_at_time(self, run_time, run_method):
        unix_seconds = time.mktime(run_time.timetuple()) + run_time.microsecond/1E6
        event_running = self.scheduler.enterabs(unix_seconds, 1, run_method, ())
        self.scheduler_thread = threading.Thread(target=self.scheduler.run)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        return event_running

    # Used to cancel a current module.
    def cancel_run(self):
        os.kill(os.getpid(), signal.SIGKILL)
