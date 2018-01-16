# README #
### Languages: Python, MongoDB

This repo was written for the purposes of generating summary data based on a unity game json file log and android app json file log. This is used at the West Health Institute's Emmersiv team.

## Setup
Please run pip install -r requirements.txt. This will install all necessary dependencies. 

## Documentation
* FileWatcher.py is the master script. To start the scheduler, please start FileWatcher.py first.
* All modules that a user would like to be run by the scheduler must be a subclass of DatabaseModule.
* Modules to be executed must be dropped into ./modules directory.
* Refer to DatabaseModule.py for requirements on subclassing your own Modules
* Also, refer to ./modules/Tester.py for an example of how to create your own modules.

## Behavior
* Moving a file into ./modules directory will load it and assign it to the scheduler
* Deleting a file from ./modules will call close on the module and remove it from memory as well as the scheduler.

## Known Issues
* If a file is moved away from the modules directory, versus being deleted this module will not detect the file move\
and will continue to keep the module running and loaded in memory

* If a file is put into the ./modules directory, it should not be deleted immedietely. There is a race condition as \
this module does not lock files. Please allow a few seconds after a file insertion to delete the file.

## Functionality
Running FileWatcher will automatically call on sched_unityappsummary and sched_assessmentappsummary and usersessionsummary.py, which use corresponding files in the lib folder. These will constantly update the MongoDB database with data entries from the clinical team. The usersessionsummary_alltextgenerator.py will be used to generate text summary file. Otherwise the usersessionsummary script will update a third collection within the MongoDB that can be connected to the web app.

* See /analytics_pymongo_code/ repo for some scripts on analyzing behavior during the space and zombie games.
* See /emmersiv_webappcharts/ repo for the front end display of all the data using highCharts.

#### Analytics:
There were two games: a space runner game and a zombie game that had certain actions built into it and certain behavioral mechanisms that the team wanted to monitor. All actions/logs are gathered using the scheduler. 

The analytics directory will then run setup of the data, and then analysis of the zombie and space game.
