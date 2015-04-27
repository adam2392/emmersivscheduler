# README #

##Setup## 
Please run pip install -r requirements.txt. This will install all necessary dependencies. 

##Documentation##
* FileWatcher.py is the master script. To start the scheduler, please start FileWatcher.py first.
* All modules that a user would like to be run by the scheduler must be a subclass of DatabaseModule.
* Modules to be executed must be dropped into ./modules directory.
* Refer to DatabaseModule.py for requirements on subclassing your own Modules
* Also, refer to ./modules/Tester.py for an example of how to create your own modules.

##Behavior##
* Moving a file into ./modules directory will load it and assign it to the scheduler
* Deleting a file from ./modules will call close on the module and remove it from memory as well as the scheduler.

##Known Issues##
* If a file is moved away from the modules directory, versus being deleted this module will not detect the file move\
and will continue to keep the module running and loaded in memory

* If a file is put into the ./modules directory, it should not be deleted immedietely. There is a race condition as \
this module does not lock files. Please allow a few seconds after a file insertion to delete the file.

