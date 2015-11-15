#!/usr/bin/env python
""" Python Algorithm 
@author Written By: Adam Li

@Brief : These python modules will 
	1. connect to the emmersiv db
	2. get all the distinct usernames
	3. filter and calculate duration of play for each user

Filtered by username.

"""
#Import modules needed
import os, pymongo, scipy, numpy as np
from datetime import datetime

conn = None
db = None
isConnected = False

''' 
Function: GameDuration 

@brief: This function queries the db for each user 
within userList to return the total play duration of a user on the game console
for the games within gameList.

@params: 
- db: the database to query
- userList: a list of users to return play duration's for
- gameList: the list of games, we want the play duration for. If passed in 0, then return total play duration

@return:
returns a list of the total play durations
'''
def gameDuration(db, userList, game):
	#initialize indexing variables and return lists
	index = 0
	duration = {}

	#converts into a list, to handle case of only passing in 1 user, or multiple users
	if isinstance(userList, basestring):
		userList = {userList}	

	#loop through each user
	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		#Check if return the duration of a game, or the entire play
		if game is 0:
			#get all distinct SON time/date on that certain user -> sort
			userTime = coll.distinct('timestamp')
		else:
			games = coll.find({"tag" : game})	
			userTime = list(spaceGames.distinct('timestamp'))

		if len(userTime) > 0:
			userTime.sort()

			#convert unix to local time
			begin = userTime[1]
			end = userTime[len(userTime)-1]

			duration[index] = round((end - begin) / 3600, 4)

			#update variables and lists
			userTime[:] = []
		else:
			duration[index] = 0

		#update game index	
		index = index + 1

	if len(duration) == 1:
		duration = duration[0]
		
	#return lists of game duration play
	return duration


'''
Function: getObstacleSets

@brief: This function queries the db for each user 
within userList and for a certain difficulty/mode finds the obstacle sets that player hard.
Should order by time 

@params: 
- db: the database to query
- userList: a list of users 
- difficulty
- mode

@return:
returns a list of the different obstacle sets
'''
def getObstacleSets(db, userList, mode, difficulty):
	#initialize indexing variables and return lists
	userIndex = 0
	obstacleList = {}
	startTime = {}

	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users
	
	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		#find all documents in the set summary with a specific mode and specific difficulty
		spaceGame = coll.find({"tag":"endlessgame", "meta.eventtype":"setsummary", 
		 	"meta.specialmode":mode, "meta.setmetadata.difficulty":difficulty})

		#should already be sorted time stamps for starttime
		start = spaceGame.distinct("meta.starttime")

		startTime[userIndex] = start
		
		#initilize empty temporary list to hold obstacle sets for a certain user
		tempList = list({})
		for time in start:
			#find the specific collection with that time stamp
			spaceGame = coll.find({"tag":"endlessgame", "meta.eventtype":"setsummary", 
		 	"meta.specialmode":mode, "meta.setmetadata.difficulty":difficulty, "meta.starttime":time})

			obstacle = spaceGame.distinct("meta.setmetadata.name")	#get obstacle name

			tempList = tempList + obstacle
			
		#stores list of all obstacle names that occur in order of time
		obstacleList[userIndex] = tempList

		print tempList

		''' NEED TO HANDLE PROBLEM OF REPEATED OBSTACLE SETS but at DIFFERENT TIME POINTS '''
		#got all the distinct obstacles
		if True: #(len(x) for x in obstacleList[userIndex])== (len(x) for(startTime[userIndex]):
			print "all good!"
		
		#there are repeat obstacles... have to find them and order them by timestamp
		else:
			tempList = list({})

			for time in startTime[userIndex]:
				#get collections of all sets with the starttime
				allSets = coll.find({"tag":"endlessgame", "meta.eventtype":"setsummary", 
				"meta.specialmode":mode, "meta.setmetadata.difficulty":difficulty, "meta.starttime":time})

				#get the obstacleSet
				obstacleSet = allSets.distinct("meta.setmetadata.name")
				obstacleSet = [str(x) for x in obstacleSet]

				tempList = tempList + obstacleSet

			#update the obstacle list with all the different sets played by user	
			obstacleList[userIndex] = tempList
			startTime[userIndex] = start

		#update userIndex and loop through again
		userIndex += 1

	return obstacleList, startTime



''' Find the number of times user gets hit in spacegame'''
def numSpaceHits(db, userList, mode):
	#initialize indexing variables and return lists
	userIndex = 0
	numMistakes = {}
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users

	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())
		
		spaceGames = coll.find({"tag":"endlessgame", "meta.eventtype" : "hitevent"})

		#get the count of how many doucments referenced by zombieGames cursor
		numMistakes[userIndex] = spaceGames.count()

		# if numMistakes[userIndex] > 0:
		# 	print users.lower(), " hit ", numMistakes[userIndex], " times in the space game :("
		# else:
		# 	print users.lower(), " did not make any mistakes in the game, or they did not play"
		userIndex = userIndex + 1
	return numMistakes

''' Analyze the tutorial response time events '''
def tutResponse(db, userList):
	#initialize indexing variables and return lists
	userIndex = 0
	avgeResponseTime = {}
	sdResponseTime = {}
	
	if isinstance(userList, basestring):
		userList = {userList}	#converts to list, so that for loop can occur

	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		#find all documents for the tutorial response event
		spaceTut = coll.find({"tag":"endlessgame", "meta.eventtype":"tutorialresponseevent"})

		#get all response time's 
		responseTime = spaceTut.distinct("meta.responsetime")

		avgeResponseTime[userIndex] = np.average(responseTime)
		sdResponseTime[userIndex] = np.std(responseTime) 

		userIndex += 1
	
	return avgeResponseTime, sdResponseTime

''' Analyze Half-Time Performance '''
def timeElapsed(db, userList, halforset, mode, difficulty):
	userIndex = 0
	timeElapsed = {}
	coinsCount = {}

	if isinstance(userList, basestring):
		userList = {userList}	#converts to list, so that for loop can occur

	#use numSpaceHits(db, userList, halfTime) to get the nubmer of hits after halftime
	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		#time elapsed is different for halftime and the rest of the game
		if halforset == "half":
			#find all documents for the tutorial response event
			spaceGame = coll.find({"tag":"endlessgame", "meta.eventtype":"halftimesummary"})
		elif halforset == "set":
			#find all documents for the tutorial response event
			spaceGame = coll.find({"tag":"endlessgame", "meta.eventtype":"setsummary", 
			"meta.specialmode":mode, "meta.setmetadata.difficulty":difficulty})

		#get the total time to reach half time
		timeElapsed[userIndex] = spaceGame.distinct("meta.timeelapsed")

		userIndex += 1

	return timeElapsed

''' Analyze coins performance during the crisis mode '''
def crisisCoins(db, userList, mode, difficulty):
	userIndex = 0
	timeElapsed = {}
	coinsCount = {}
	
	#return list of coins count
	redCoins = {}
	blueCoins = {}
	yellowCoins = {}
	redCoins2 = {}
	blueCoins2 = {}
	yellowCoins2 = {}


	if isinstance(userList, basestring):
		userList = {userList}	#converts to list, so that for loop can occur

	#use numSpaceHits(db, userList, halfTime) to get the nubmer of hits after halftime
	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		#find all documents in the set summary with a specific mode and specific difficulty
		spaceGame = coll.find({"tag":"endlessgame", "meta.eventtype":"setsummary", 
			"meta.specialmode":mode, "meta.setmetadata.difficulty":difficulty})

		#get total number of collected coins
		redCoins[userIndex] = spaceGame.distinct("meta.setmetadata.redcount")
		blueCoins[userIndex] = spaceGame.distinct("meta.setmetadata.bluecount")
		yellowCoins[userIndex] = spaceGame.distinct("meta.setmetadata.yellowcount")

		#these coins come outside of "setmetadata"
		redCoins2[userIndex] = spaceGame.distinct("meta.redpickupcount")
		blueCoins2[userIndex] = spaceGame.distinct("meta.bluepickupcount")
		yellowCoins2[userIndex] = spaceGame.distinct("meta.yellowpickupcount")

		coinsCount[userIndex] = redCoins[userIndex] + blueCoins[userIndex] + yellowCoins[userIndex]


		#get the total time to reach half time
		timeElapsed[userIndex] = spaceGame.distinct("meta.timeelapsed")

		userIndex += 1
		
	return redCoins, blueCoins, yellowCoins

''' Check what happens when user dies '''
def checkDeath(db, userList, mode, difficulty):
	userIndex = 0
	timeElapsed = {}
	coinsCount = {}

	#return list of coins count
	redCoins = {}
	blueCoins = {}
	yellowCoins = {}

	if isinstance(userList, basestring):
		userList = {userList}	#converts to list, so that for loop can occur
	
	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		#find all documents in the set summary with a specific mode and specific difficulty
		spaceGame = coll.find({"tag":"endlessgame", "meta.eventtype":"setsummary", 
			"meta.specialmode":mode, "meta.setmetadata.difficulty":difficulty, "meta.died":True})

		#user did die at least once
		if spaceGame.count() > 0:
			#check #coins and what type
			#get total number of collected coins
			redCoins[userIndex] = spaceGame.distinct("meta.setmetadata.redcount")
			blueCoins[userIndex] = spaceGame.distinct("meta.setmetadata.bluecount")
			yellowCoins[userIndex] = spaceGame.distinct("meta.setmetadata.yellowcount")

			####### CHECK OBSTACLES AND FIGURE OUT HOW TO DETERMINE WHICH OBSTACLES KILLED 



		#user did not die
		else:
			redCoins[userIndex] = -1
			blueCoins[userIndex] = -1
			yellowCoins[userIndex] = -1
		
		userIndex += 1

	return redCoins, blueCoins, yellowCoins


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
		#testing the definitions.
		userList = ['adamspace_testgood2']
		#weightHit = 0.75
		#weightShot = 0.25
		mode = 1
		difficulty = 1

		# duration = playDuration(db, userList)
		spaceDuration = gameDuration(db, userList, 0)

		numHits = numSpaceHits(db, userList, 'n/a')
		avgeResponseTime, sdResponseTime = tutResponse(db, userList)
		
		#loop through difficulty modes: easy, medium, hard
		for difficulty in range(0,3): #(0, 4)
			#loop through special modes: none, redcrisis, bluecrisis, yellowcrisis, lowspeed, highspeed, reversecontrols
			for mode in range(0,4): #(0, 7)
				timeForSet = timeElapsed(db, userList, "set", mode, difficulty)
				redCoins, blueCoins, yellowCoins = crisisCoins(db, userList, mode, difficulty)
				redCoinsDeath, blueCoinsDeath, yellowCoinsDeath = checkDeath(db, userList, mode, difficulty)
				obstacles, startTimes = getObstacleSets(db, userList, mode, difficulty)

				userIndex = 0
				for user in userList:
					
					print "1) For:", userList[userIndex], timeForSet[userIndex], "the time elapsed for mode =",mode, "and difficulty =", difficulty
					print "2) For:", userList[userIndex], redCoins[userIndex], blueCoins[userIndex], yellowCoins[userIndex], "the red, blue, yellow coins colleceted for mode =",mode, "and difficulty =", difficulty
					print "3) For:", userList[userIndex], obstacles[userIndex], "the obstacles for mode =",mode, "and difficulty =", difficulty
					print "4) For:", userList[userIndex], startTimes[userIndex], "the obstacles for mode =",mode, "and difficulty =", difficulty

					if redCoinsDeath[userIndex] is -1:
						print user, "did not die"
					else:
						print "3) For:", userList[userIndex], redCoinsDeath[userIndex], blueCoinsDeath[userIndex], yellowCoinsDeath[userIndex], "the red, blue, yellow cooins collected before dying", "for mode =", mode, "and difficulty =", difficulty
					
					userIndex += 1

		
		#print userList, "weightHit: ", weightHit, "weightzShot: ", weightShot
		print spaceDuration, "space play duration (hrs)"
		print numHits, "number of times user hit wall"
		print avgeResponseTime, "average response time in tutorial"
		print sdResponseTime, "sd of response time in tutorial"