__author__ = 'Adam Li'
import datetime as dt
import sys
import pymongo
import traceback
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
class UserScheduledGenSummaries(DatabaseModule):     
    # Define any class specific init requirements. Make sure to call super init on the parent class.
    def __init__(self):
        super(UserScheduledGenSummaries, self).__init__()
        self.runtime = 1
        self.module_description = "Scheduled queries on user sessions......"

    # This method will be called when a module needs to close. Here you can ensure that you finish any operations
    # before your module is killed by the scheduler.
    # Again please make sure that you call close on the parent class.
    # At the end of your close statement signal to the scheduler that you can proceed with killing the module by
    # calling finish_closing() on yourself.
    # This is a function defined in the parent class and should not be overwritten.
    # You have 30 seconds to close your module, otherwise it will be killed and your work will be lost.
    def close(self):
        super(UserScheduledGenSummaries, self).close()
        # Arguments to close cleanly
        # Call to indicate close clean
        self.finish_closing()

    # Called by the scheduler.
    # The purpose of this function is to allow the module to let the scheduler know what time it must be run at.
    # If you require that a module runs for example, every day at 8 PM call self.scheduleManager.run_at_time at the end
    # of your close statement. This will ensure that the function is run again at the specified time.
    def setup(self):
        super(UserScheduledGenSummaries, self).setup()
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
        super(UserScheduledGenSummaries, self).start()

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
            print "Creating userSessionSummary."
            sessionSummary = 'userSessionSummary'

            #drop the collection now that it has been finished using
            try:
                db.drop_collection(sessionSummary)
            except:
                print "----> WTF? ", traceback.print_exc()

            # try to create collection, if it already exists, it will throw an exception
            try:
                db.create_collection(sessionSummary)

                if debug_on:
                    print "Creating collection ", sessionSummary, " ---> OK!"

            except pymongo.errors.CollectionInvalid:
                print 'Collection ', sessionSummary, ' already exists.'

            # collection either created, or already exists, query into collection
            gamecoll = pymongo.collection.Collection(db, 'gameSessionSummary')
            appcoll = pymongo.collection.Collection(db, 'assessmentSessionSummary')
            maincoll = pymongo.collection.Collection(db, sessionSummary)
            coll = pymongo.collection.Collection(db, 'appsessions')

            # get the list of all users from the beginning app sessions
            userList = coll.find({}).distinct("userId")
            userList = [x.lower() for x in userList]
            userList = list(set(userList))

            # loop through each user to generate the list of mongoID's
            for user in userList:
                # get a list of mongo IDs for each user in each collection; check upper and lower case
                gameMongoIds = gamecoll.find({'userId':user.upper()}).distinct("_id")
                appMongoIds = appcoll.find({'userId':user.upper()}).distinct("_id")

                if not gameMongoIds:
                    gameMongoIds = gamecoll.find({'userId':user.lower()}).distinct("_id")
                if not appMongoIds:
                    appMongoIds = appcoll.find({'userId':user.lower()}).distinct("_id")

                # assign mongoIds to null if no unity game was played, or no assessment app was played
                if not gameMongoIds:
                    gameMongoIds = "null"
                if not appMongoIds:
                    appMongoIds = "null"

                # build out the result that will be written to file
                result = {
                    "userId": user.lower(),
                    "gameSessions": gameMongoIds,
                    "appSessions": appMongoIds,
                    "timeCreated":
                }

                # check if user document is already in the collection
                userInDb = maincoll.find({'userId': user}).distinct("_id")
                # if not userInDb:
                #     userInDb = maincoll.find({'userId': user.upper()}).distinct("_id")

                # if it is not, then insert it
                if not userInDb:
                    #collection created, or exists, try to insert into that collection
                    try:
                        # insert into the collection, the generated summary
                        maincoll.insert(result)
                        
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
                # # if it is inside, then update it
                # else:
                #     try:
                #         # insert into the collection, the generated summary
                #         maincoll.update({'_id' : userInDb},
                #                         {"$push" : {"gameSessions" : gameMongoIds}},
                #                         {"$push" : {"appSessions" : appMongoIds}}
                #                         )
                        
                #         if debug_on:
                #             print "Insertion finished for ", user, ' and session: ', objectId

                #     #exceptions for inserting into the temporary collection 
                #     except pymongo.errors.OperationFailure:
                #         if debug_on:
                #             print user, " already in there"
                #             # print "----> OP failed"
                #     except pymongo.errors.InvalidName:
                #             print "----> Invalid Name"
                #     except:
                #             print "----> WTF? ", traceback.print_exc() 

            ## add the check to make sure no repeating session IDs or etc.

        if __name__ == '__main__':
            self.close()
        else:
            self.setup()
        # Call close after your module has exited to kill the process. Or, reschedule it for another round

if __name__ == '__main__':
    testrun = UserScheduledGenSummaries()

    testrun.run()