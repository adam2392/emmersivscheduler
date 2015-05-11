__author__ = 'Adam Li'
import datetime
import sys
import pymongo
import json
import os
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

		userList = gameColl.find({}).distinct("userId")

		for user in userList:
			# grab the summary object
			sessions = gameColl.find({'userId':user}).distinct("sessionId")

			summaries = []
			for session in sessions:
				summary = gameColl.find({'userId':user, 'sessionId':session}).distinct('summary')
				# summary = sorted(summary, key=lambda k: k['id']) # sort by quesiton ID
				summaries.append(summary) # append to the return summaries list

			# build out the result that will be written to file
			result = {
				"userId": user,
				"summaries": summaries
			}

			# write this out to a file
			filename = user+'_gameSummary.json'

			# try deleting file (if it exists)
			try:
				os.remove(filename)
			except OSError:
				pass
				
			with open(filename, 'w') as outfile:
				json.dump(result, outfile, cls=MyEncoder)


		## add the check to make sure no repeating session IDs or etc.

			