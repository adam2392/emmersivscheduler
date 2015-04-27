__author__ = 'pbelon'
import sys
import time
import os
import imp
from multiprocessing import Process
import inspect
import logging
from watchdog.observers import Observer
import watchdog.events
import zmq
from libs import Config
from libs.DatabaseModule import DatabaseModule
from threading import Thread
import psutil
import datetime as dt
import glob
import importlib

# Class used to watch file system and restart, start, and kill module processes
class Watcher(watchdog.events.FileSystemEventHandler):
    all_python_files = []
    module_pid_dict = {}
    socket = None
    modules_path = os.path.join(os.getcwd(), Config.FILEWATCHER_CONFIG['MODULES_DIRECTORY'])
    logger = None
    accept_new_modules = True

    # Initializes the class and pre-loads all existing modules.
    # Initializes the zmq bus to communicate to modules.
    def __init__(self):
        self.logger = logging.getLogger('EM')
        formatter = logging.Formatter('%(asctime)s : %(message)s')
        fileHandler = logging.FileHandler(Config.FILEWATCHER_CONFIG['LOG_FILE'], mode='a')
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)

        self.logger.info('Filewatcher PID : ' + str(os.getpid()))
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind(Config.FILEWATCHER_CONFIG['MSG_QUEUE_STRING'])
        files = [f for f in os.listdir(self.modules_path)]
        for f in files:
            if f.endswith('.py'):
                basename = os.path.basename(f)
                basename_without_extension = basename[:-3]
                process_object = self.spawn_module_process(basename, basename_without_extension)
                self.set_module_pid(basename, process_object)

    # Used to respawn modules when they have been modified.
    # NOTE: Python cannot remove imports once they are imported.
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            self.logger.info('File modified: '+event.src_path)
            basename = os.path.basename(event.src_path)
            process_object = self.get_process_object_for_module(basename)
            self.send_kill_message_to_pid(process_object, basename)
            # self.remove_module_from_pid_dict(basename)
            basename_without_extension = basename[:-3]
            module_process_object = self.spawn_module_process(basename, basename_without_extension)
            self.set_module_pid(basename, module_process_object)


    # Used to start a module once it has been dropped into the file.
    # TODO: Test to make sure that all os behave the same and that files dropped in are treated as file creations.
    def on_created(self, event):
        if event.src_path.endswith('.py'):
            self.logger.info('File created: '+event.src_path)
            basename = os.path.basename(event.src_path)
            basename_without_extension = basename[:-3]
            module_process_object = self.spawn_module_process(basename, basename_without_extension)
            self.set_module_pid(basename, module_process_object)

    # Used to kill a module process if it has been deleted from directory.
    def on_deleted(self, event):
        if event.src_path.endswith('.py'):
            self.logger.info("File deleted: "+event.src_path)
            basename = os.path.basename(event.src_path)
            module_process_object = self.get_process_object_for_module(basename)
            self.send_kill_message_to_pid(module_process_object, basename)

    # TODO: Implement on_moved
    def on_moved(self, event):
        if event.src_path.endswith('.py'):
            self.logger.info("File moved: "+event.src_path)

    # Helper method to spawn a module process
    def spawn_module_process(self, filename, module_name):
        if not self.accept_new_modules:
            return None
        module_path = os.path.join(os.getcwd(), Config.FILEWATCHER_CONFIG['MODULES_DIRECTORY'], filename)
        try:
            mod = imp.load_source(module_name, module_path)
        except:
            files = [f for f in os.listdir(self.modules_path)]
            print files
            return None
        self.logger.info("Loaded module: "+module_name)
        for name, obj_in_module in inspect.getmembers(mod):
            if inspect.isclass(obj_in_module):
                # Check to make sure that inspected object is a subclass of DatabaseModule and is not DatabaseModule
                if issubclass(obj_in_module, DatabaseModule) and (obj_in_module.__name__ != 'DatabaseModule'):
                    # instantiate the class because it must be a DatabaseModule subclass
                    DatabaseModule_subclass = obj_in_module()
                    # Make sure that subclass has implemented setup
                    setup_method = getattr(DatabaseModule_subclass, "setup", None)
                    if callable(setup_method):
                        process = Process(target=DatabaseModule_subclass.setup)
                        process.start()
                        self.socket.send("Created: "+str(process.pid))
                        self.logger.info("Module " + module_name + " assigned PID: " + str(process.pid))
                        return process
                    else:
                        self.logger.error("Module "+module_name+" did not have attribute setup")

    # Helper method to remove a module from dictionary of module names and PID's
    def remove_module_from_pid_dict(self, module_path):
        del self.module_pid_dict[module_path]
        self.logger.info("Removed " + module_path + " from internal cache")

    # Helper method to return pid for a given module
    def get_pid_for_module(self, module_path):
        return self.module_pid_dict[module_path].pid

    def get_process_object_for_module(self, module_path):
        return self.module_pid_dict[module_path]

    def get_process_object_for_module(self, module_path):
        return self.module_pid_dict[module_path]

    # Helper method to set the pid for a given module in internal cache.
    def set_module_pid(self, module_path, process):
        if process is not None:
            self.module_pid_dict[module_path] = process

    def kill_remaining_processes(self):
        for key_module_path in self.module_pid_dict:
            self.send_kill_message_to_pid(self.module_pid_dict[key_module_path], key_module_path)

    # Used to kill a module. Will do spawn a background thread to continuosly check for module to close
    # If module doesn't close within 30 seconds it will kill it.
    def send_kill_message_to_pid(self, process, module_path):
        self.logger.info("Module process " + str(process.pid) + " sent kill message")
        t = Thread(target=self.check_for_process_end, args=(process.pid, module_path))
        self.socket.send(str(process.pid))
        #t.daemon = True
        #t.start()

    def stop_loading_modules(self):
        self.accept_new_modules = False

    def close_self(self):
        self.logger.info('Closing FileWatcher')
        self.stop_loading_modules()
        self.kill_remaining_processes()

    # Keep process object around to send terminate message
    # Do in background thread to allow yourself to use the scheduler.
    def check_for_process_end(self, process, module_path):
        self.socket.send(str(process.pid))
        p = psutil.pid_exists(process.pid)
        seconds_elapsed = 0
        run_time = dt.datetime.now()
        while p is True:
            p = psutil.pid_exists(process.pid)
            seconds_elapsed = dt.datetime.now() - run_time
            if seconds_elapsed.total_seconds() > 30:
                self.logger.info('Total close time for process: ' + str(process.pid) + ' elapsed. Terminating...')
                process.terminate()
                process.join()
                #self.remove_module_from_pid_dict(module_path)
                break

# TODO: Seems as is if a module is moved away from modules directory it does not get a notification.
# TODO: Need to watch for modules not existing.
if __name__ == "__main__":

    path = sys.argv[1] if len(sys.argv) > 1 else Config.FILEWATCHER_CONFIG['MODULES_DIRECTORY']
    watcher = Watcher()
    observer = Observer()
    observer.schedule(watcher, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        watcher.close_self()
    observer.join()
    watcher.logger.info('Watcher exiting...waiting timeout to terminate zombies')
