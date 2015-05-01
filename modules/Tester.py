# __author__ = 'patrickbelon'
# import datetime as dt
# import sys
# sys.path.append("..") #add higher directory to python modules path
# import pymongo
# import json

# from models.appsession import FileUpload
# from models.appsession import AppSession
# from libs.DatabaseModule import DatabaseModule


# # The following class is an example of how you would write your own module to access a database

# # Create a class to run your database query code and ensure that the class inherits from DatabaseModule.
# # The DatabaseModule class defines a series of methods that are required to perform and abstract scheduling and
# # running database queries. As well as being able to handle scenarios where modules must be started/restarted or killed.
# class Test(DatabaseModule):

#     # Define any class specific init requirements. Make sure to call super init on the parent class.
#     def __init__(self):
#         super(Test, self).__init__()
#         self.module_description = "Scheduled queries on sessions."

#     # This method will be called when a module needs to close. Here you can ensure that you finish any operations
#     # before your module is killed by the scheduler.
#     # Again please make sure that you call close on the parent class.
#     # At the end of your close statement signal to the scheduler that you can proceed with killing the module by
#     # calling finish_closing() on yourself.
#     # This is a function defined in the parent class and should not be overwritten.
#     # You have 30 seconds to close your module, otherwise it will be killed and your work will be lost.
#     def close(self):
#         super(Test, self).close()
#         # Arguments to close cleanly

#         # Call to indicate close clean
#         self.finish_closing()

#     # Called by the scheduler.
#     # The purpose of this function is to allow the module to let the scheduler know what time it must be run at.
#     # If you require that a module runs for example, every day at 8 PM call self.scheduleManager.run_at_time at the end
#     # of your close statement. This will ensure that the function is run again at the specified time.
#     def setup(self):
#         super(Test, self).setup()
#         now = dt.datetime.now()
#         # Change delta to schedule every delta periods...
#         delta = dt.timedelta(seconds=10)

#         t = now.time()
#         run_time = dt.datetime.combine(now, t) + delta
#         self.scheduleManager.run_at_time(run_time, self.run)

#         # Make sure you call start on super after setup
#         super(Test, self).start()

#     # This method is called by the scheduler to run your queries.
#     # Call close after you are finished running your query to let the scheduler know that you are finished.
#     # This method will be run on a different thread than your module.
#     def run(self):
#         isConnected = False

#         # Try to connect with the mongodb server to the main db: emmersiv
#         try:
#             conn = pymongo.MongoClient()
#             db = conn.emmersiv
#             print "Connected to MongoDB server"
#             isConnected = True
#         except:
#             print "Connection Failed..."

#         # If connected, read each file in the data directory and dump the data into the DB
#         if isConnected == True:
#             print 'Running queries on new session IDs...'
        
#             # initialize query class
#             app = UnityAppSessionSummary()

            

#             #creating collection, and if already created insert into it
#             summarycoll = pymongo.collection.Collection(db, 'results')
        
#             #get the 'events' array 
#             eventDocs = coll.find({"userId" : user, "sessionId" : sessionId}).distinct("events")

#             tempName = user+"_"+sessionId

#             #try to create a collection with name held by users
#             #if not, then it already exists
#             try:
#                 db.create_collection(tempName)
                
#                 if debug_on:
#                     print 'Creating collection', tempName, '---> OK'

#             except pymongo.errors.CollectionInvalid:
#                 print 'Collection ', tempName, ' already exists'
#             #collection created, or exists, try to insert into that collection
#             try:
#             #get the collection of that user
#             coll = pymongo.collection.Collection(db, tempName)

#             #loop through userDocs and insert all JSON data into that collection for 'user'
#             for doc in eventDocs:
#                 coll.insert(doc)
            
#             if debug_on:
#                 print "Insertion finished for ", tempName

#         #exceptions for inserting into the temporary collection 
#         except pymongo.errors.OperationFailure:
#                 print "----> OP failed"
#         except pymongo.errors.InvalidName:
#                 print "----> Invalid Name"
#         except:
#                 print "----> WTF? ", traceback.print_exc() 

#         # return the name of the temporary collection
#         return tempName



#         self.close()
#         # Call close after your module has exited to kill the process. Or, reschedule it for another round