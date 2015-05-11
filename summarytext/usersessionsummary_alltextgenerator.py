__author__ = 'Adam Li'
import datetime
import sys
import pymongo
import json
import os
from bson.objectid import ObjectId
from time import mktime

class MyEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return int(mktime(obj.timetuple()))
		if isinstance(obj, datetime.timedelta):
			return int(mktime(obj.timetuple()))

		return json.JSONEncoder.default(self, obj)


if __name__ == '__main__':
	isConnected = False
	debug_on = False

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
		# create a collection for the 'gameSessionSummary' collection
		gameColl = pymongo.collection.Collection(db, 'gameSessionSummary')
		appColl = pymongo.collection.Collection(db, 'appSessionSummary')
		userColl = pymongo.collection.Collection(db, 'userSessionSummary')

		userList = userColl.find({}).distinct("userId")

		summaries = []
		for user in userList:
			print "looking at ", user

			# grab all mongo IDs
			gameSessions = userColl.find({'userId':user}).distinct("gameSessions")
			appSessions = userColl.find({'userId':user}).distinct("appSessions")

			# existingObjectIds = []
			# for session in gameSessions:
			# 	existingObjectIds.append(session)

			# loop through to collect the game data
			gameSummaries = []
			if not isinstance(gameSessions[0], basestring):
				for session in gameSessions:
					summary = gameColl.aggregate([
						{"$match" :
							{"_id" : ObjectId(session)}
						},
						{"$group" :
							{"_id" : "$_id",
							 "application" : {"$push" : "$application"},
							 "sessionId" : {"$push" : "$sessionId"},
							 "userId" : {"$push" : "$userId"},
							 "summary" : {"$push" : "$summary"}
							}
						}
					])
					result = summary["result"]

					for i in range(0, len(result)):
						temp = result[i]
						result[i] = {
							"application" : temp["application"],
							"sessionId" : temp["sessionId"],
							"userId" : temp["userId"],
							"summary" : temp["summary"]
						}

					gameSummaries.append(result) # append to the return summaries list

			# loop through to collect the app data
			appSummaries = []
			if not isinstance(appSessions[0], basestring):
				for session in appSessions:
					summary = appColl.aggregate([
						{"$match" :
							{"_id" : ObjectId(session)}
						},
						{"$group" :
							{"_id" : "$_id",
							 "application" : {"$push" : "$application"},
							 "sessionId" : {"$push" : "$sessionId"},
							 "userId" : {"$push" : "$userId"},
							 "summary" : {"$push" : "$sessionSummaries"}
							}
						}
					])
					result = summary["result"]

					for i in range(0, len(result)):
						temp = result[i]
						result[i] = {
							"application" : temp["application"],
							"sessionId" : temp["sessionId"],
							"userId" : temp["userId"],
							"summary" : temp["summary"]
						}

					appSummaries.append(result) # append to the return summaries list

			if not gameSummaries:
				gameSummaries = "null"

			if not appSummaries:
				appSummaries = "null"

			# build out the result that will be written to file
			result = {
				"userId": user,
				"gameSummaries": gameSummaries,
				"appSummaries": appSummaries
			}

			summaries.append(result)
			
		# end of for user in userList

	# write this out to a file
	filename = 'sessionSummary.json'

	# try deleting file (if it exists)
	try:
		os.remove(filename)
	except OSError:
		pass
		
	with open(filename, 'w') as outfile:
		json.dump(summaries, outfile, cls=MyEncoder)

		## add the check to make sure no repeating session IDs or etc.

			