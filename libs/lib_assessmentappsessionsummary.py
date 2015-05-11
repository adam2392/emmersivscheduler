__author__ = "adamli"
""" Library file for generating summary data for the assessment app for Emmersiv team.
@author Written By: Adam Li

@Brief : These python modules will connect to the db, create a temporary collection and run 
queries on the input log json files. 
"""
#import statements
import datetime
import pymongo
import json
import traceback
from time import mktime
from bson.objectid import ObjectId
debug_on = False

class MyEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return int(mktime(obj.timetuple()))
		if isinstance(obj, datetime.timedelta):
			return int(mktime(obj.timetuple()))

		return json.JSONEncoder.default(self, obj)

class AssessmentAppSessionSummary():
	# returns number of time user has this sessionId and list of session Ids
	# def numberOfSessions(self, db, userId):
		# try:
		# 	#connect to the collection 'appsessions' within 'emmersiv' db
		# 	coll = pymongo.collection.Collection(db, 'appsessions')

		# 	# query the db for "application" : assessment
		# 	assessment = coll.aggregate([
		# 		{"$match" : 
		# 			{"application" : "assessment",
		# 			 "userId" : userId
		# 			}
		# 		},
		# 		{"$group" : 
		# 			{"_id": "$startTime",
		# 			 "sessionId" : {"$push" : "$sessionId"}
		# 			}
		# 		},
		# 		{"$sort" : {"_id" : 1}}
		# 	])
		# 	result = assessment['result']

		# 	sessionCount = len(result)

		# 	### Debugging Prints ###
		# 	if debug_on:
		# 		print "Looking at session id: "
		# 		print "The number of sessions is: ", sessionCount, "\n\n"

		# 	return sessionCount
		# except:
		# 	print "----> WTF? ", traceback.print_exc() 
		# 	return "error"
	def getSessionId(self, db, userId, objectId):
		try:
			#connect to the collection 'appsessions' within 'emmersiv' db
			coll = pymongo.collection.Collection(db, 'appsessions')

			#query for the user
			sessionId = coll.find({"userId" : userId, "_id" : ObjectId(objectId)}).distinct("sessionId")

			### Debugging Prints ###
			if debug_on:
				print "Looking at user: ", userId, " for user sessionId: ", sessionId
			
			if not sessionId:
				return 'null'	

			return sessionId[0]
		except:
			print "----> WTF? ", traceback.print_exc() 
			return "error"

	# This method is used to obtain a list of all session ID's for a certain user
	def getObjectIds(self, db, userId):
		try:
			# super(UnityAppSessionSummary, self).getSessionIds(db, user)
			sessionList = {}

			#connect to the collection 'appsessions' within 'emmersiv' db
			coll = pymongo.collection.Collection(db, 'appsessions')

			#query for the user
			userId = coll.find({"userId" : userId})

			#get distinct sessionId's and convert to list from queryset
			sessionList= userId.distinct("_id")
			objectList = []

			for session in sessionList:
				objectList.append(session)

			### Debugging Prints ###
			if debug_on:
				print "Looking at user: ", user, " for user object id's: ", sessionList
				
			return objectList
		except:
			print "----> WTF? ", traceback.print_exc() 
			return "error"

	def createTempColl(self, db, user, objectId):
		#connect to the collection 'appsessions' within 'emmersiv' db
		coll = pymongo.collection.Collection(db, 'appsessions')

		#get the 'events' array 
		eventDocs = coll.find({"userId" : user, "_id" : ObjectId(objectId)}).distinct("events")

		tempName = user+"_"+ str(objectId)

		#try to create a collection with name held by users
		#if not, then it already exists
		try:
			db.create_collection(tempName)
			
			if debug_on:
				print 'Creating collection', tempName, '---> OK'
		except pymongo.errors.CollectionInvalid:
			if debug_on:
				print " "
			# print 'Collection ', tempName, ' already exists'
		#collection created, or exists, try to insert into that collection
		try:
			#get the collection of that user
			coll = pymongo.collection.Collection(db, tempName)

			#loop through userDocs and insert all JSON data into that collection for 'user'
			for doc in eventDocs:
				coll.insert(doc)
			
			if debug_on:
				print "Insertion finished for ", tempName

		#exceptions for inserting into the temporary collection	
		except pymongo.errors.OperationFailure:
			if debug_on:
				print " "
				# print "----> OP failed", traceback.print_exc() 
		except pymongo.errors.InvalidName:
				print "----> Invalid Name"
		except:
				print "----> WTF? ", traceback.print_exc() 

		# return the name of the temporary collection
		return tempName

	def dropTempColl(self, db, tempName):
		#drop the collection now that it has been finished using
		try:
			db.drop_collection(tempName)
			if debug_on:
				print 'Dropping collection', tempName, '---> OK \n\n'
		except:
			print "----> WTF? ", traceback.print_exc() 

	# query for when the sessino start for a specific session ID?
	def sessionStart(self, db, userId, objectId):
		# try:
			#create temporary collection 		
			tempName = self.createTempColl(db, userId, objectId)	

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			startSession = colltemp.find({"eventType" : "SubjectLoginEvent"}).distinct('timestamp')

			if len(startSession) > 1:
				print "more than 1 start session?..."

			if not startSession:
				return 'N/A'

			# reformat to unix time
			startSession = mktime(startSession[0].timetuple())

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", tempName
				print "start timestamp: ", startSession, "\n\n"

			self.dropTempColl(db, tempName)

			return startSession
		# except:
		# 	print "----> WTF? ", traceback.print_exc() 
		# 	return "error"


	# query for when the session end for a specific session ID?
	def sessionEnd(self, db, userId, objectId):
		# try:
			#create temporary collection 		
			tempName = self.createTempColl(db, userId, objectId)	

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			endSession = colltemp.find({}).distinct('timestamp')
			
			if not endSession:
				return 'N/A'

			endTime = max(endSession)

			# reformat into unix time
			endTime = mktime(endTime.timetuple())

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", tempName
				print "end timestamp: ", endTime, "\n\n"

			self.dropTempColl(db, tempName)

			return endTime
		# except:
		# 	print "----> WTF? ", traceback.print_exc() 
		# 	return "error"

	# determine the total session duration
	def sessionDuration(self, start, end):
		# try:
			if start == 'N/A' or end == 'N/A' :
				return 'N/A'

			userDuration = end-start
			# print userDuration
			return userDuration
		# except:
		# 	print "----> WTF? ", traceback.print_exc() 
		# 	return "error"

	def summaryQA(self, db, userId, objectId):
		# try:
			#create temporary collection 		
			tempName = self.createTempColl(db, userId, objectId)	

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)

			# query the db for "application" : assessment
			summary = colltemp.aggregate([
				{"$match" : 
					{"eventType" : "AnswerSubmittedEvent"}
				},
				{"$group" : 
					{"_id":"$timestamp",
					 "summaryQA" : {"$push" : "$meta"}
					}
				},
				{"$sort" : {"_id" : 1}}
			])
			result = summary['result']


			for i in range(0,len(result)):
				summ = result[i]
				result[i] = {
					"timestamp" : summ["_id"],
					"summaryQA" : summ["summaryQA"][0]
				}
				
			self.dropTempColl(db, tempName)

			return result
		# except:
		# 	print "----> WTF? ", traceback.print_exc() 
		# 	return "error"


	def getSessionSummary(self, db, uid, oid):
		# list of tuples of (_id, _question, _answer)
		listOfQuestions = {
			"sessionId": self.getSessionId(db, uid, oid),
			"startTime": self.sessionStart(db, uid, oid),
			"stopTime": self.sessionEnd(db, uid, oid),
			"duration": self.sessionDuration(self.sessionStart(db, uid, oid), self.sessionEnd(db, uid, oid)),
			"qna": self.summaryQA(db, uid, oid)
		}

		# create the final response json object to return
		response = {"userId" : uid,
					"sessionId" : self.getSessionId(db, uid, oid),
					"application" : "eventlog",
					"summary" : listOfQuestions
				   }

		# print response
		# print json.dumps(response, cls = MyEncoder, sort_keys=True)
		return listOfQuestions

'''Run the main script...
runs overall Function
'''
# Check if this is the main program running, or is an imported module
if __name__ == '__main__':
	isConnected = False

	# Try to connect with the mongodb server 
	try:
		conn = pymongo.MongoClient()
		db = conn.emmersiv
		print "Connected to MongoDB server"
		isConnected = True
	except:
		print "Connection Failed..." 

	# If connected, read each file in the data directory and dump the data into the DB
	if isConnected == True:
		user = raw_input("Please enter in the username: ")
		sessionId = raw_input("Please enter in the sessionId: ")
		time01 = raw_input("Please enter in the first timeStamp: ")
		time02 = raw_input("Please enter in the second timeStamp: ")

		user = "jofa"

		#create instance of the class
		app = AssessmentAppSessionSummary()

		objectIds = app.getObjectIds(db, user)
		count = 0
		for objectId in objectIds:
			print objectId
			sessionSummary = app.getSessionSummary(db, user, objectId)
			count = count + 1
			if count is 1:
				break

			

