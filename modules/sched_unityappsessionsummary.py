__author__ = 'Adam Li'
import datetime as dt
import sys
import pymongo
import json

sys.path.append("..") #add higher directory to python modules path
from models.appsession import FileUpload
from models.appsession import AppSession
from libs.DatabaseModule import DatabaseModule
from libs.lib_unityappsessionsummary import UnityAppSessionSummary as app

# The following class is an example of how you would write your own module to access a database

# Create a class to run your database query code and ensure that the class inherits from DatabaseModule.
# The DatabaseModule class defines a series of methods that are required to perform and abstract scheduling and
# running database queries. As well as being able to handle scenarios where modules must be started/restarted or killed.
class UnityScheduledGenSummaries(DatabaseModule):
    # Define any class specific init requirements. Make sure to call super init on the parent class.
    def __init__(self):
        super(UnityScheduledGenSummaries, self).__init__()
        self.runtime = 1
        self.module_description = "Scheduled queries on unity app sessions......"

    # This method will be called when a module needs to close. Here you can ensure that you finish any operations
    # before your module is killed by the scheduler.
    # Again please make sure that you call close on the parent class.
    # At the end of your close statement signal to the scheduler that you can proceed with killing the module by
    # calling finish_closing() on yourself.
    # This is a function defined in the parent class and should not be overwritten.
    # You have 30 seconds to close your module, otherwise it will be killed and your work will be lost.
    def close(self):
        super(UnityScheduledGenSummaries, self).close()
        # Arguments to close cleanly
        # Call to indicate close clean
        self.finish_closing()

    # Called by the scheduler.
    # The purpose of this function is to allow the module to let the scheduler know what time it must be run at.
    # If you require that a module runs for example, every day at 8 PM call self.scheduleManager.run_at_time at the end
    # of your close statement. This will ensure that the function is run again at the specified time.
    def setup(self):
        super(UnityScheduledGenSummaries, self).setup()
        now = dt.datetime.now()
        if self.runtime is 1:
            delta = dt.timedelta(seconds=5)
        else:
            # Change delta to schedule every delta periods...
            delta = dt.timedelta(seconds=7200)

        t = now.time()
        run_time = dt.datetime.combine(now, t) + delta
        self.scheduleManager.run_at_time(run_time, self.run)

        # Make sure you call start on super after setup
        super(UnityScheduledGenSummaries, self).start()

    # This method is called by the scheduler to run your queries.
    # Call close after you are finished running your query to let the scheduler know that you are finished.
    # This method will be run on a different thread than your module.
    def run(self):
        isConnected = False
        debug_on = False

        if self.runtime is 1:
            self.runtime = 2

        # Try to connect with the mongodb server to the main db: emmersiv
        try:
            conn = pymongo.MongoClient()
            db = conn.emmersiv

            if debug_on:
                print "Connected to MongoDB server"
                
            isConnected = True
        except:
            print "Connection Failed..."

        # If connected, read each file in the data directory and dump the data into the DB
        if isConnected == True:
            print "Creating gameSessionSummary."
            gameSessionSummary = 'gameSessionSummary'

            # try to create collection, if it already exists, it will throw an exception
            try:
                db.create_collection(gameSessionSummary)

                if debug_on:
                    print "Creating collection 'gameSessionSummary' ---> OK!"

            except pymongo.errors.CollectionInvalid:
                print 'Collection ', gameSessionSummary, ' already exists.'

            # collection either created, or already exists, query into collection
            maincoll = pymongo.collection.Collection(db, 'appsessions')
            coll = pymongo.collection.Collection(db, gameSessionSummary)

            # # initialize query class
            # app = unityapp()

            #initialize common queries and variables
            unityquery = {"application" : "eventlog"}
            time01 = 0
            time02 = 0

            # get list of users from the unity app in the main collection
            gameUserList = maincoll.find(unityquery).distinct("userId")
            
            #instantiate instance of UnityAppSessionSummary
            myapp = app()

            for user in gameUserList:
                #query for session Ids for all users from unity app
                sessionIds = myapp.getSessionIds(db, user)

                # Now get a list of session Ids already within the collection 'game session'
                existingSessions = coll.find(unityquery).distinct("sessionId")

                if debug_on:
                    print 'Running queries on ', user
                    print 'existing sessions from start: ', existingSessions, '\n'
                
                for sessionId in sessionIds:
                    ### Debug messages
                    if debug_on:
                        print 'Running queries on new session ID: ', sessionId

                    # if the session is not in the existing collection -> insert
                    if sessionId not in existingSessions:
                        # access unityappsessionsummary api to query results of specific user and session
                        summary = myapp.getSessionSummary(db, user, sessionId)         

                        print 'Running queries on new session ID: ', sessionId, ' for sched unity.'

                        #collection created, or exists, try to insert into that collection
                        try:
                            # insert into the collection, the generated summary
                            coll.insert(summary)
                            
                            if debug_on:
                                print "Insertion finished for ", user, ' and session: ', sessionId

                        #exceptions for inserting into the temporary collection 
                        except pymongo.errors.OperationFailure:
                               print " "
                                # print "----> OP failed"
                        except pymongo.errors.InvalidName:
                                print "----> Invalid Name"
                        except:
                                print "----> WTF? ", traceback.print_exc() 

                    elif debug_on:
                        print sessionId, " already exists \n"
                #end for sessionId
            #end for user

        if __name__ == '__main__':
            self.close()
        else:
            self.setup()
        # Call close after your module has exited to kill the process. Or, reschedule it for another round

if __name__ == '__main__':
    testrun = UnityScheduledGenSummaries()

    testrun.run()
