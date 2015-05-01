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
				return 'N/A'
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
				return 'N/A'
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
			elapsed = peerInstruction.distinct("meta.elapsed")
			instructionId = peerInstruction.distinct("meta.peerInstructionID")

			if len(elapsed) > 1 or len(instructionId) > 1:
				print "Error! peer instruction occured more than once!"

			self.dropTempColl(db, tempName)

			if not instructionId:
				return 'N/A'
			else:
				peerModuleTuple = str((instructionId[0], elapsed[0])).strip('[]')

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "Peer Instruction ID: ", instructionId
				print "Peer module instruction elapsed timestamp: ", elapsed, "\n\n"

			return peerModuleTuple 
		except:
			return "error"

	# Find out which games user attmpted to play
	def sessionGamesAttempt(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)
					
			#### query starts: successfully inserted into the db 
			colltemp = pymongo.collection.Collection(db, tempName)
			eventGame = colltemp.aggregate([
				{"$match" : 
					{"meta._t" : "GameSelectionEvent"}
				},
				{"$group" : 
					{"_id":"$timestamp",
					 "game": {"$push" : "$meta.game"}
					}
				},
				{"$sort" : {"_id" : 1}}
				])
			gameList = eventGame['result']

			gamesAttempted = []

			# loop through gameList and append games (to get rid of _id)
			for game in gameList:
				gamesAttempted.append(str(game["game"]).strip('[]'))

			# gamesAttempted = str(gamesAttempted).strip('[]')

			self.dropTempColl(db, tempName)

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The games played are: ", gameList, "\n\n"

			return gamesAttempted
		except:
			return "error"

	# Find out how much time spent waiting for game in line
	def sessionGameWait(self, db, user, sessionId):
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
					 "elapsed" : {"$push": "$meta.elapsed"},
					 "game": {"$push" : "$meta.game"}
					}
				},
				{"$sort" : {"_id" : 1}
				}
				])

			gameWaitTuple = lineWait["result"]

			gamesWait = []

			# loop through gameList and append games (to get rid of _id)
			for game in gameWaitTuple:
				if len(game["elapsed"]) > 1:
					print game["elapsed"]
					print "Error game wait session!"
				waitTup = (game["game"][0], game["elapsed"][0])
				gamesWait.append(waitTup)

			gamesWait = str(gamesWait).strip('[]')

			self.dropTempColl(db, tempName)
			
			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The games played are: ", lineWait, "\n\n"

			return gamesWait
		except:
			return "error"

	# Find out hhow long each mini game was played for
	def sessionMiniGameDuration(self, db, user, sessionId):
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
					 "elapsed" : {"$push" : "$meta.elapsed"},
					 "game" : {"$push" : "$meta.game"}
					}
				},
				{"$sort" : {"_id" : 1}}
				])

			miniGameTuple = miniGame["result"]

			# initialize list and indicing variable
			miniGame = []

			#loop through results and extract id and elapsed
			for game in miniGameTuple:
				if len(game["elapsed"]) > 1:
					print "Error mini game duration!"
				
				gameTup = (game["game"], game["elapsed"][0])
				miniGame.append(gameTup)

			miniGame = str(miniGame).strip('[]')

			self.dropTempColl(db, tempName)
			
			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The games played are: ", miniGameTuple, "\n\n"

			return miniGame
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

			scenes = []

			# loop through result and add necessary fields
			for scene in sceneTuple:
				sceneTup = (scene["scene"][0], scene["elapsed"][0])
				scenes.append(sceneTup)

			scenes = str(scenes).strip('[]')

			self.dropTempColl(db, tempName)	

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The scenes shown and how long are: ", sceneTuple, "\n\n"

			return scenes
		except:
			return "error"


	# Find out which questions were presented during the session
	def sessionQuestions(self, db, user, sessionId):
		try:	
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			questionIds = []

			#### query starts: successfully inserted into the db 
			colltemp = pymongo.collection.Collection(db, tempName)
			captureEvent = colltemp.find({"tag":"startcaptureevent"})
			questions = captureEvent.distinct("eventType")

			# find the question Ids
			for question in questions:
				# this is a question event...
				if "Question" in question:
					# variables to control looping through meta data
					index = 0
					firstFound = 0
					startcomma = 0
					endcomma = 0

					# find the commas (the question ids are between commas)
					startcomma = question.index(",")
					endcomma = question.index(",", startcomma+1)

					questionIds.append(question[startcomma+2:endcomma])

			questionIds = str(questionIds).strip('[]')

			self.dropTempColl(db, tempName)

			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The question Ids are: ", questionIds, "\n\n"

			return questionIds

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

			return responses
		except:
			return "error"

	# Find out many times line wait was canceled
	def sessionLineWaitCancel(self, db, user, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db 
			colltemp = pymongo.collection.Collection(db, tempName)
			responseEvent = colltemp.aggregate([					
				{"$match" : 
					{"meta._t" : "LineWaitEvent", "meta.successful" : False}
				},
				{"$group" : 
					{"_id":"$timestamp", 
					 "line length" : {"$push" : "$meta.lineLength"},
					 "game" : {"$push" : "$meta.game"}
					}
				},
				{"$sort" : {"_id" : 1}
				}
			])
			lineTuple = responseEvent["result"]

			lineWait = []

			# loop through result and add necessary fields
			for line in lineTuple:
				waitTup = (line["game"][0], line["line length"][0])
				lineWait.append(waitTup)

			lineWait = str(lineWait).strip('[]')

			self.dropTempColl(db, tempName)
			
			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The line wait for games and length are: ", lineTuple, "\n\n"

			return lineWait
		except:
			return "error"

	# Find skeletal information between two time points
	def sessionSkeleton(self, db, user, time01, time02, sessionId):
		try:
			#create temporary collection 		
			tempName = self.createTempColl(db, user, sessionId)

			#### query starts: successfully inserted into the db -> now query for start time
			colltemp = pymongo.collection.Collection(db, tempName)
			# timestamps = colltemp.find({"meta._t" : "SkeletonJoints"}).distinct("timestamp").sort()
			# timestamps = sorted(i for i in timestamps if i >= time01 and i <= time02)
			# print timestamps

			skeletonJoints = colltemp.aggregate([					
				{"$match" : 
					{"meta._t" : "SkeletonJoints", "timestamp" : {"$gte" : time01, "$lte" : time02}}
				},
				{"$group" : 
					{"_id":"$timestamp", 
					 "hipLeft" : {"$addToSet" : "$meta.hipLeft"}, 
					 "kneeLeft"	: {"$addToSet" : "$meta.kneeLeft"},
					 "ankleLeft" : {"$addToSet" : "$meta.ankleLeft"},
					 "hipRight"	: {"$addToSet" : "$meta.hipRight"},
					 "kneeRight" : {"$addToSet" : "$meta.kneeRight"},
					 "ankleRight" : {"$addToSet" : "$meta.ankleRight"},
					 "hipCenter" : {"$addToSet" : "$meta.hipCenter"},
					 "shoulderCenter" : {"$addToSet" : "$meta.shouldCenter"},
					 "head"	: {"$addToSet" : "$meta.head"},
					 "spine" : {"$addToSet" : "$meta.spine"},
					 "shoulderLeft"	: {"$addToSet" : "$meta.shouldLeft"},
					 "shoulderRight" : {"$addToSet" : "$meta.shouldRight"},
					 "elbowLeft" : {"$addToSet" : "$meta.elbowLeft"},
					 "elbowRight" : {"$addToSet" : "$meta.elbowRight"},
					 "wristLeft" : {"$addToSet" : "$meta.wristLeft"},
					 "wristRight" : {"$addToSet" : "$meta.wristRight"},
					 "footLeft"	: {"$addToSet" : "$meta.footLeft"},		
					 "footRight" : {"$addToSet" : "$meta.footRight"},
					 "handLeft"	: {"$addToSet" : "$meta.handLeft"},		
					 "handRight" : {"$addToSet" : "$meta.handRight"}
					}
				},
				{"$sort" : {"_id" : 1}},
			])
			skeletonCoords = skeletonJoints["result"]

			self.dropTempColl(db, tempName)
			
			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId, " examining skeleton joints."
				#print "The line wait for games and length are: ", lineTuple, "\n\n"

			return skeletonCoords	
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
			
			### Debugging Prints ###
			if debug_on:
				print "Looking at session id: ", sessionId
				print "The session data summary is: ", sessionData, "\n\n"

			return sessionData
		
		except:
			return "error"


	def getSessionSummary(self, db, uid, sid, t01=0, t02=0):
		listSummary = []	# list of sessions summaries

		# list of tuples of (_id, _question, _answer)
		listOfQuestions = [
			(1, "What date/time did the session start?", self.sessionStart),
			(2, "What date/time did the session end?", self.sessionEnd),
			(3, "What was the duration of the session?", self.sessionDuration),
			(4, "What was the calibration angle of the sensor?", self.sessionCalibrationAngle),
			(5, "How much time was spent trying to open the arcade door?", self.sessionEnterArcadeTime),
			(6, "Which peer instruction module was played? How long did it last?", self.sessionPeerInstruction),
			(7, "Which games did the user attempt to play?", self.sessionGamesAttempt),
			(8, "For each play, how long did the user have to wait in line?", self.sessionGameWait),
			(9, "For each mini game played, what was duration of play?", self.sessionMiniGameDuration),
			(10, "Which social vignettes did the user watch during the session? How long did each last?", self.sessionSocialScene),
			(11, "Which questions were presented to the user during this session?", self.sessionQuestions),
			(12, "How did the user respond to each of the questions presented?", self.sessionQuestionResponse),
			(13, "How many times did the user cancel waiting in line? For which games? What was the line length?", self.sessionLineWaitCancel),
			(14, "Grab skeleton frames between t1 and t2.", self.sessionSkeleton),
			(15, "Did the user skip the playback of the social vignette during remediation? Which vignette?", self.sessionSocialSceneSkips),
			(16, "Did the player initiate a shutdown of the app during the session?", self.sessionPlayerShutdown),
			(17, "The session summary object?", self.sessionSummary)
		]

		errorList = []
		for (_id, _question, _method) in listOfQuestions:
			if _id is 14: #session skeleton
				result = {
						"id": _id,
						"question": _question,
						"result": _method(db, uid, t01, t02, sid)
					 }
			elif _id is 3:	#session duration
				result = {
						"id": _id,
						"question": _question,
						"result": _method(self.sessionStart(db, uid, sid), self.sessionEnd(db, uid, sid))
					 }
			else:
				result = {
						"id": _id,
						"question": _question,
						"result": _method(db, uid, sid)
					 }

			if result["result"] is 0:
				result["result"] = 0
			elif not result["result"]:
				result["result"] = "NULL"

			# append a list of error questions to error log
			if "error" in str(result["result"]):
				errorList.append(result["id"])

			listSummary.append(result)

		# generate an error document to insert into the response
		errorResult = {
			"id": "Errors",
			"question": "Which questions produced errors?",
			"result": errorList
		}
		listSummary.append(errorResult)
		
		# create the final response json object to return
		response = {"userId" : uid,
					"sessionId" : sid,
					"application" : "eventlog",
					"summary" : listSummary
				   }
		# print response
		# print json.dumps(response, cls = MyEncoder)
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
		time01 = raw_input("Please enter in the first timeStamp: ")
		time02 = raw_input("Please enter in the second timeStamp: ")

		#create instance of the class
		app = UnityAppSessionSummary()

		sessionSummary = app.getSessionSummary(db, user, sessionId, time01, time02)