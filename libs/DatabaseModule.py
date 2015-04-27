__author__ = 'pbelon'
import os
import logging
import zmq
import ScheduleManager
from libs import Config


# Base class for all modules.
# This module defines a set of methods that must be overwritten by the module
# but as well some methods that cannot be overwritten.
class DatabaseModule(object):
    scheduleManager = None
    logger = None
    module_description = None

    # Creates internal scheduling.
    # Overriding: Please make sure to call super.init otherwise the schedule manager will
    # not get instantiated
    def __init__(self):
        self.scheduleManager = ScheduleManager.SchedManager()
        self.logger = logging.getLogger('EM')

    # Called by the scheduler if the module needs to reload or stop running.
    # Please override and provide a clean way of closing
    # Make sure that when you override you call the super implementation
    def close(self):
        self.logger.info('Module: %s PID: Close called %s', self.module_description, str(os.getpid()))

    def finish_closing(self):
        self.logger.info('Module: %s PID: Called final close %s', self.module_description, str(os.getpid()))
        self.scheduleManager.cancel_run()

    # Called by scheduler to run your module.
    # Please place all query calls in your sub class implementation
    def run(self):
        self.logger.info('Module: %s PID: Running %s', self.module_description, str(os.getpid()))

    # DO NOT OVERRIDE
    # Protected
    def start(self):
        self.logger.info('Module: %s PID: Start %s', self.module_description, str(os.getpid()))
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.SUBSCRIBE, '')
        socket.connect(Config.MODULE_CONFIG['MSG_QUEUE_STRING'])
        while True:
            try:
                msg = socket.recv()
                msg_parsed = msg.split(':')
                if len(msg_parsed) > 1:
                    pass
                else:
                    if int(msg_parsed[0]) == os.getpid():
                        self.close()
            except KeyboardInterrupt:
                pass
                #self.close()

    # setup code. This will be called on your module once its dropped into the ./modules directory.
    # Pass the schedule manager the time that you want your code to run.
    # If you want your module to run continuously place a call to re-assign a run time
    # with the schedule manager at the end of the run statement.
    def setup(self):
        self.logger.info('Module: %s PID: Loaded %s', self.module_description, str(os.getpid()))



