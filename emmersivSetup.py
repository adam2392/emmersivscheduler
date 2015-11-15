#!/usr/bin/env python

""" Python Algorithm Step 01 to store all data into MongoDb
and Filter Names and Store filtered names in MongoDB
@author Written By: Adam Li
@Brief : These python modules will 
	1. connect to the emmersiv db
	2. create 'alldata' collections with all the data from a game-play setting
	3. get a list of all distinct usernames
	3. filter and create collections within 'emmersiv' for each username
@Updates:
- Combine emmersivProcess.py with filterName
- -> emmersivSetUp.py
"""
#directory Path to find all the log files/data from a game session ***Probably will be changed***
dataDirPath = "C:\\Users\\Adam\\Desktop\\Data\\"

#import modules needed
import os, pymongo, json, traceback

#initialize connection variables
conn = None
db = None

'''Function: dumpLinesIntoDatabase
@input:
	- lines: the list of all JSON data from all log files
@output:
	- returns the # of okay inserts, duplicate inserts and failed inserts
	- just puts all data into the collection 'alldata'
'''
def dumpLinesIntoDatabase(lines):

	countOK = 0
	countDUP = 0
	countFAIL = 0
	total = 0

	for line in lines:
		line = line[line.find("{") : ]
		line = (line.replace("ObjectId(" , "").replace(")","")).lower()
		try:
			jsonObj = json.loads(line)
		except ValueError:
			jsonObj = json.loads(json.dumps(line))
		total += 1
		
		try:
			_id = db.alldata.insert(jsonObj)
			countOK += 1
		except pymongo.errors.DuplicateKeyError:
			countDUP += 1
		except:
			countFAIL += 1

	# returns
	return (countOK, countDUP, countFAIL)

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
		print 'Reading Data Directory...', dataDirPath

		# get the list of files in the data dir
		lsDir = os.listdir(dataDirPath)
		for eachFile in lsDir:

			# if this file is a game event log
			if ".log" in eachFile:
				print '->', 'reading:', eachFile 

				pathFile = dataDirPath + eachFile
				linesInFile = open(pathFile).readlines()
				print dumpLinesIntoDatabase(linesInFile)

		# try querying db for distinct userId's
		try:
			allUsers = db.alldata.distinct('userid')
		except pymongo.errors.TypeError:
			print "----> key is not an instance of basestring!"
		except:
			print "----> huh?", traceback.print_exc()

		#loop through all distinct users
		for users in allUsers:
			#convert all to lowercase
			lowerUsers = users.lower()

			print "Currently looking at ", lowerUsers

			#get the JSON data for particular user and convert to list
			userDocs = list(db.alldata.find({'userid': users}))

			#try to create a collection with name held by users
			#if not, then it already exists
			try:
				db.create_collection(lowerUsers)
				print 'Creating collection', lowerUsers, '---> OK'
			except pymongo.errors.CollectionInvalid:
				print 'Collection ', lowerUsers, ' already exists'

			#collection created, or exists, try to insert into that collection
			try:
				#get the collection of that user
				coll = pymongo.collection.Collection(db, lowerUsers)

				#loop through userDocs and insert all JSON data into that collection for 'user'
				for doc in userDocs:
					coll.insert(doc)
				print "Insertion finished for ", lowerUsers
			except pymongo.errors.OperationFailure:
					print "----> OP failed"
			except pymongo.errors.InvalidName:
					print "----> Invalid Name"
			except:
					print "----> WTF? ", traceback.print_exc() 

			'''Filtering Kinect Data By Username'''
			coll = pymongo.collection.Collection(db, users.lower())
			print "Currently looking at", users.lower(), " to filter kinect data"

			#find all skeletal data and convert to a list
			kinectData = list(coll.find({"meta._t": "skeletonjoints"}))
			newCollName = users.lower() + "_kinectdata"	#name of the new collection to be made

			#try to create and insert all kinect data into a new collection
			try:
				#iterate through all collected kinect data
				for line in kinectData:
					#check that line is not empty
					if line is not None:
						#create collection 
						db.create_collection(newCollName)
						newColl = pymongo.collection.Collection(db, newCollName)

						#and insert JSON documents
						newColl.insert(line)

						print "Insertion finished for ", newCollName
			
				print "No Insertion for ", newCollName
			
			except pymongo.errors.CollectionInvalid:
				print 'Collection ', newCollName, ' already exists'
			except pymongo.errors.OperationFailure:
				print "----> OP insertion failed"
			except pymongo.errors.InvalidName:
				print "----> Invalid insertion Name"
			except:
				print "----> WTF? ", traceback.print_exc() 
	
	#isConnected == True
		# userList = ['emmersiv', 'milan', 'brendan']
		# duration = runScripts.playDuration(db, userList, isConnected)
		# gameDuration = runScripts.gameDuration(db, userList, 'n/a', isConnected)