__author__ = "adamli"

""" Python Methods for Analyzing the Unity App and all the game data
@author Written By: Adam Li

@Brief : These python modules will 
	1. connect to the emmersiv db
	2. run a certain query
	3. return data in json format
"""
#import statements
import datetime
import pymongo
import json
import sys
import traceback
from time import mktime
from bson import json_util
debug_on = False

class MyEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return int(mktime(obj.timetuple()))
		if isinstance(obj, datetime.timedelta):
			return int(mktime(obj.timetuple()))

		return json.JSONEncoder.default(self, obj)

class UnityAppSessionSummary():
	# This method is used to obtain a list of all session ID's for a certain user
	def getSessionIds(self, db, user):
		try:
			# super(UnityAppSessionSummary, self).getSessionIds(db, user)
			sessionList = {}

			#connect to the collection 'appsessions' within 'emmersiv' db
			coll = pymongo.collection.Collection(db, 'appsessions')

			#query for the user
			userId = coll.find({"userId" : user})

			#get distinct sessionId's and convert to list from queryset
			sessionList= list(userId.distinct("sessionId"))

			### Debugging Prints ###
			if debug_on:
				print "Looking at user: ", user, " for user sesssion id's: ", sessionList
				
			return sessionList
		except:
			return "error"

	def createTempColl(self, db, user, sessionId):
		#connect to the collection 'appsessions' within 'emmersiv' db
		coll = pymongo.collection.Collection(db, 'appsessions')
		
		#get the 'events' array 
		eventDocs = coll.find({"userId" : user, "sessionId" : sessionId}).distinct("events")

		tempName = user+"_"+sessionId

		#try to create a collection with name held by users
		#if not, then it already exists
		try:
			db.create_collection(tempName)
			
			if debug_on:
				print 'Creating collection', tempName, '---> OK'
		except pymongo.errors.CollectionInvalid:
			if debug_on:
				print ""
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
				print ""
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

	# Find out what date/time did a certain session start
	def sessionStart(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)	

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			startApp = colltemp.find({"tag":"application start"})
			startTime = startApp.distinct("timestamp")

			if len(startTime) > 1:
				print "there is more than 1 instance of application start!"
			
			# print startTime
			if not startTime:
				print "N/A at start for ", sessionId, user
				return 'N/A'
			else:
				startTime = mktime(startTime[0].timetuple())

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", tempName
				print "start timestamp: ", startTime, "\n\n"

			self.dropTempColl(db, tempName)

			#end of userList for loop
			return startTime 
		except:
			return "error"

	# Find out what date/time did a certain session end
	def sessionEnd(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db -> now query for end time
			try:
				colltemp = pymongo.collection.Collection(db, tempName)
				endApp = colltemp.find({"meta._t" : "ShutdownEvent"})
				timeStamp = (endApp.distinct("timestamp"))[0]
			except:
				# second heuristic
				try:
					endApp = colltemp.find({"tag":"application quit"})
					timeStamp = (endApp.distinct("timestamp"))[0]
				except:
					try:
						# third heuristic
						endApp = colltemp.find({}).distinct("timestamp")
						timeStamp = max(endApp)
					except:
						print "----> WTF? ", traceback.print_exc() 
			
			endTime = mktime(timeStamp.timetuple())

			self.dropTempColl(db, tempName) 

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "end timestamp: ", timeStamp, "\n\n"

			#end of userList for loop
			return endTime
		except:
			return "error"

	# determine the total session duration
	def sessionDuration(self, start, end):
		try:
			if start == 'N/A' or end == 'N/A' :
				return 'N/A'

			userDuration = end-start
			# print userDuration
			return userDuration
		except:
			return "error"

	# Find out what the calibration angle was for the session
	def sessionCalibrationAngle(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db 
			colltemp = pymongo.collection.Collection(db, tempName)
			configEvent = colltemp.find({"meta._t" : "CalibrationConfigEvent", "meta.message" : "calibration complete"})
			calibAngle = configEvent.distinct("meta.angle")

			if len(calibAngle) > 1:
				print "Calibrated angle more than once!"

			self.dropTempColl(db, tempName)

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "Calibration angle: ", calibAngle, "\n\n"
			
			if not calibAngle:
				return 'null'
			else:
				return calibAngle[0]
		except:
			return "error"

	# Find out how much time spent trying to open arcade door
	def sessionEnterArcadeTime(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db 
			colltemp = pymongo.collection.Collection(db, tempName)
			enterArcade = colltemp.find({"meta._t" : "EnterArcadeEvent"})
			elapsed = enterArcade.distinct("meta.elapsed")

			if len(elapsed)>1:
				print "Error! Entered arcade event occurs twice!"

			self.dropTempColl(db, tempName)

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "Entering arcade elapsed timestamp: ", elapsed, "\n\n"

			if not elapsed:
				return 'null'
			else:
				return elapsed[0]
		except:
			return "error"

	# Find out which peer instruction module user watched
	def sessionPeerInstruction(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db 
			colltemp = pymongo.collection.Collection(db, tempName)
			peerInstruction = colltemp.find({"meta._t" : "WatchPeerInstruction"})
			# elapsed = peerInstruction.distinct("meta.elapsed")
			instructionId = peerInstruction.distinct("meta.peerInstructionID")

			if len(elapsed) > 1 or len(instructionId) > 1:
				print "Error! peer instruction occured more than once!"

			self.dropTempColl(db, tempName)

			if not instructionId:
				return 'null'
			else:
				peerModule = instructionId[0]

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "Peer Instruction ID: ", instructionId
				print "Peer module instruction elapsed timestamp: ", elapsed, "\n\n"

			return peerModule
		except:
			return "error"

	# Find out which games user attmpted to play
	def sessionGamesPlayed(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)
					
			#### query starts: successfully inserted into the db 
			colltemp = pymongo.collection.Collection(db, tempName)

			miniGame = colltemp.aggregate([
				{"$match" : 
					{"meta._t" : "GamePlayEvent"}
				},
				{"$group" : 
					{"_id":"$timestamp", 
					 "duration" : {"$push" : "$meta.elapsed"},
					 "game" : {"$push" : "$meta.game"}
					}
				},
				{"$sort" : {"_id" : 1}}
				])

			gameList = miniGame['result']

			for i in range(0, len(gameList)):
				result = gameList[i]
				gameList[i] = {
					"game" : result["game"],
					"duration" : result["duration"]
				}

			self.dropTempColl(db, tempName)

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The games played are: ", gameList, "\n\n"

			if not gameList:
				return "null"

			return gameList
		except:
			return "error"

	# Find out line wait info for each game
	def sessionLineWait(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)
					
			#### query starts: successfully inserted into the db 
			colltemp = pymongo.collection.Collection(db, tempName)

			lineWait = colltemp.aggregate([
				{"$match" : 
					{"meta._t" : "LineWaitEvent"}
				},
				{"$group" : 
					{"_id":"$timestamp", 
					 "duration" : {"$push": "$meta.elapsed"},
					 "game": {"$push" : "$meta.game"},
					 "successful": {"$push" : "$meta.successful"},
					 "length" : {"$push" : "$meta.lineLength"}
					}
				},
				{"$sort" : {"_id" : 1}
				}
				])

			lineInfo = lineWait['result']

			for i in range(0, len(lineInfo)):
				result = lineInfo[i]
				lineInfo[i] = {
					"game" : result["game"],
					"duration" : result["duration"],
					"length" : result["length"], 
					"successful" : result["successful"]
				}

			self.dropTempColl(db, tempName)

			if not lineInfo:
				return "null"

			return lineInfo
		except:
			return "error"

	# Find out which social scene was played and for how long
	def sessionSocialScene(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db
			colltemp = pymongo.collection.Collection(db, tempName)
			socialScene = colltemp.aggregate([
				{"$match" : 
					{"meta._t" : "WatchSocialModelingScene"}
				},
				{"$group" : 
					{"_id":"$timestamp", 
					 "elapsed" : {"$push" : "$meta.elapsed"}, 
					 "scene" : {"$push" : "$meta.sceneNumber"}
					}
				},
				{"$sort" : {"_id" : 1}}
				])

			sceneTuple = socialScene["result"]

			for i in range(0, len(sceneTuple)):
				result = sceneTuple[i]
				sceneTuple[i] = {
					"sceneId" : result["scene"],
					"duration" : result["elapsed"],
				}


			self.dropTempColl(db, tempName)	

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The scenes shown and how long are: ", sceneTuple, "\n\n"

			if not sceneTuple:
				return "null"

			return sceneTuple
		except:
			return "error"

	# Find out users's response to each question
	def sessionQuestionResponse(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)
			
			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			responseEvent = colltemp.aggregate([					
				{"$match" : 
					{"meta._t" : "QuestionResponseEvent"}
				},
				{"$group" : 
					{"_id":"$meta.questionID", 
					 "attempt count" : {"$push" : "$meta.attemptCount"},
					 "prompting level" : {"$push" : "$meta.promptingLevel"},
					 "answer index" : {"$push" : "$meta.answerIndex"},
					 "correct answer" : {"$push" : "$meta.correctAnswer"},
					 "response time" : {"$push" : "$meta.responseTime"},
					 "timestamp" : {"$push" : "$timestamp"}
					}
				},
				{"$sort" : {"timestamp" : 1}}
			])
			responses = responseEvent["result"]

			self.dropTempColl(db, tempName)
			
			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The question responses are: ", responses, "\n\n"

			if not responses:
				return "null"

			return responses
		except:
			return "error"

	# Find out how much time spent trying to open arcade door
	def sessionSocialSceneSkips(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			socialScene = colltemp.aggregate([					
				{"$match" : 
					{"meta._t" : "WatchSocialModelingScene", "meta.replayCanceled" : True}
				},
				{"$group" : 
					{"_id":"$meta.sceneNumber",
					 "timestamp" : {"$push" : "$timestamp"}
					}
				},
				{"$sort" : {"timestamp" : 1}
				}
			])

			sceneIds = socialScene["result"]

			sceneSkip = []

			# loop through result and add necessary fields
			for scene in sceneIds:
				sceneSkip.append(scene["_id"])

			# sceneSkip = str(sceneSkip).strip('[]')

			self.dropTempColl(db, tempName) 
			
			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The scene numbers which were skipped are: ", sceneIds, "\n\n"

			if not sceneSkip:
				return "null"

			return sceneSkip
		except:
			return "error"

	# Find out how much time spent trying to open arcade door
	def sessionPlayerShutdown(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			shutdownEvent = colltemp.find({"meta._t" : "ShutdownEvent"})
			shutdown = shutdownEvent.distinct("meta.initiatedByPlayer")

			self.dropTempColl(db, tempName) 

			shutdown = str(shutdown).strip('[]')
			
			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The player initiated shutdown is: ", shutdown, "\n\n"

			if not shutdown:
				return False

			return shutdown
		except:
			return "error"

	# Find out how much time spent trying to open arcade door
	def sessionSummary(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			shutdownEvent = colltemp.find({"meta._t" : "ShutdownEvent"})
			sessionData = shutdownEvent.distinct("meta.sessionData")

			self.dropTempColl(db, tempName)  
			
			### Debugging Prints ###.
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The session data summary is: ", sessionData, "\n\n"

			if not sessionData:
				return "null"

			return sessionData
		
		except:
			return "error"

	def sessionKinectError(self, db, user, sessionId):
		try:
			# create temporary collection
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			kinectErrorEvent = colltemp.find({"tag": "kinecterrorevent"})
			kinectError = kinectErrorEvent.distinct("timestamp")

			if len(kinectError) > 0:
				result = True
			else:
				result = False

			self.dropTempColl(db, tempName)  

			return result
		
		except:
			print "kinect error ", traceback.print_exc() 
			return "error"

	def sessionPause(self, db, user, sessionId):
		try:
			# create temporary collection
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			pauseEvent = colltemp.find({"meta._t": "PauseEvent"})
			totalPause = pauseEvent.distinct("meta.totalPauseTime")

			self.dropTempColl(db, tempName)  

			if not totalPause:
				return "null"

			return totalPause
		except:
			print "session Pause, ", traceback.print_exc() 
			return "error"

	def getSessionSummary(self, db, uid, sid):
		# list of tuples of (_id, _question, _answer)
		listOfQuestions = {
			"sessionId": sid,
			"startTime": self.sessionStart(db, uid, sid),
			"stopTime": self.sessionEnd(db, uid, sid),
			"duration": self.sessionDuration(self.sessionStart(db, uid, sid), self.sessionEnd(db, uid, sid)),
			"angle": self.sessionCalibrationAngle(db, uid, sid),
			"elapsedArcadeDoor": self.sessionEnterArcadeTime(db, uid, sid),
			"peerInstruction": self.sessionPeerInstruction(db, uid, sid),
			"gamesPlayed": self.sessionGamesPlayed(db, uid, sid),
			"lineWait": self.sessionLineWait(db, uid, sid),
			"socialVignettes": self.sessionSocialScene(db, uid, sid),
			"qna": self.sessionQuestionResponse(db, uid, sid),
			"skippedPlayback": self.sessionSocialSceneSkips(db, uid, sid),
			"userShutdown": self.sessionPlayerShutdown(db, uid, sid),
			"sessionSummary": self.sessionSummary(db, uid, sid),
			"kinectError": self.sessionKinectError(db, uid, sid),
			"pauseTimes": self.sessionPause(db, uid, sid)
		}

		
		# create the final response json object to return
		response = {"userId" : uid,
					"sessionId" : sid,
					"application" : "eventlog",
					"summary" : listOfQuestions
				   }
		
		# response = json.dumps(response, cls = MyEncoder)
		# print response
		return response


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

		#create instance of the class
		user = 'ALZA'
		app = UnityAppSessionSummary()
		sessions = app.getSessionIds(db, user)

		for session in sessions:
			sessionSummary = app.getSessionSummary(db, user, session)