__author__ = 'Adam Li'
import datetime as dt
import sys
import pymongo
import json
from bson.objectid import ObjectId

sys.path.append("..") #add higher directory to python modules path
from models.appsession import FileUpload
from models.appsession import AppSession
from libs.DatabaseModule import DatabaseModule
from libs.lib_assessmentappsessionsummary import AssessmentAppSessionSummary as app


# The following class is an example of how you would write your own module to access a database

# Create a class to run your database query code and ensure that the class inherits from DatabaseModule.
# The DatabaseModule class defines a series of methods that are required to perform and abstract scheduling and
# running database queries. As well as being able to handle scenarios where modules must be started/restarted or killed.
class AssessmentScheduledGenSummaries(DatabaseModule):     
    # Define any class specific init requirements. Make sure to call super init on the parent class.
    def __init__(self):
        super(AssessmentScheduledGenSummaries, self).__init__()
        self.runtime = 1
        self.module_description = "Scheduled queries on assessment app sessions......"

    # This method will be called when a module needs to close. Here you can ensure that you finish any operations
    # before your module is killed by the scheduler.
    # Again please make sure that you call close on the parent class.
    # At the end of your close statement signal to the scheduler that you can proceed with killing the module by
    # calling finish_closing() on yourself.
    # This is a function defined in the parent class and should not be overwritten.
    # You have 30 seconds to close your module, otherwise it will be killed and your work will be lost.
    def close(self):
        super(AssessmentScheduledGenSummaries, self).close()
        # Arguments to close cleanly
        # Call to indicate close clean
        self.finish_closing()

    # Called by the scheduler.
    # The purpose of this function is to allow the module to let the scheduler know what time it must be run at.
    # If you require that a module runs for example, every day at 8 PM call self.scheduleManager.run_at_time at the end
    # of your close statement. This will ensure that the function is run again at the specified time.
    def setup(self):
        super(AssessmentScheduledGenSummaries, self).setup()
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
        super(AssessmentScheduledGenSummaries, self).start()

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
            print "Creating assessmentSessionSummary."
            sessionSummary = 'assessmentSessionSummary'

            # try to create collection, if it already exists, it will throw an exception
            try:
                db.create_collection(sessionSummary)

                if debug_on:
                    print "Creating collection ", sessionSummary, " ---> OK!"

            except pymongo.errors.CollectionInvalid:
                print 'Collection ', sessionSummary, ' already exists.'

            # collection either created, or already exists, query into collection
            maincoll = pymongo.collection.Collection(db, 'appsessions')
            coll = pymongo.collection.Collection(db, sessionSummary)

            # # initialize query class
            # app = unityapp()

            #initialize common queries and variables
            assessmentquery = {"application" : "assessment"}

            # get list of users from the unity app in the main collection
            gameUserList = maincoll.find(assessmentquery).distinct("userId")
            
            #instantiate instance of UnityAppSessionSummary
            myapp = app()
            # count = 0

            for user in gameUserList:
                #query for session Ids for all users from unity app
                objectIds = myapp.getObjectIds(db, user)

                # Now get a list of object Ids already within the collection 'game session'
                existingObjectID = coll.find(assessmentquery).distinct("_id")
                existingObjectIds = []
                for session in existingObjectID:
                    existingObjectIds.append(session)

                if debug_on:
                    print 'Running queries on ', user
                    print 'existing sessions from start: ', existingObjectIds, '\n'
                
                for objectId in objectIds:

                    ### Debug messages
                    if debug_on:
                        print 'Running queries on new session ID: ', ObjectId(objectId)

                    # if the session is not in the existing collection -> insert
                    if objectId not in existingObjectIds:
                        print 'Running queries on new session ID: ', objectId, ' for sched assessment.'

                        # access unityappsessionsummary api to query results of specific user and session
                        summary = myapp.getSessionSummary(db, user, objectId)         

                        # build the response JSON object
                        response = {"userId" : user,
                            "_id" : objectId,
                            "sessionId" : myapp.getSessionId(db, user, objectId),
                            "application" : "assessment",
                            "sessionSummaries" : summary
                           }

                        #collection created, or exists, try to insert into that collection
                        try:
                            # insert into the collection, the generated summary
                            coll.insert(response)
                            
                            if debug_on:
                                print "Insertion finished for ", user, ' and session: ', objectId

                        #exceptions for inserting into the temporary collection 
                        except pymongo.errors.OperationFailure:
                            if debug_on:
                                print user, " already in there"
                                # print "----> OP failed"
                        except pymongo.errors.InvalidName:
                                print "----> Invalid Name"
                        except:
                                print "----> WTF? ", traceback.print_exc() 

                    elif debug_on:
                        print objectId, " already exists \n"
                #end of for objectId in objectIds
            #end of for user

        if __name__ == '__main__':
            self.close()
        else:
            self.setup()
        # Call close after your module has exited to kill the process. Or, reschedule it for another round

if __name__ == '__main__':
    testrun = AssessmentScheduledGenSummaries()

    testrun.run()