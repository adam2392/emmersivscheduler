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
import os, pymongo, json
from datetime import datetime

conn = None
db = None
isConnected = False
''' number of shots fired for zombie game for everyone in userList 
	1. find all zombiegame documents for users
	2. find all shot events and count them per user 			'''
def numZombShots(db, userList, mode):
	#initialize indexing variables and return lists
	userIndex = 0
	numShots = {}

	normal = 'normal'
	boss = 'boss'

	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users


	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		if mode == 'normal':
			#find zombiegames and numShots using collections
			zombieShots = coll.find({"tag":"zombiegame", "meta.eventname" : "shotevent", "meta.levelstate": "normal_mode"}) #, "meta.isballready": True})
		else:
			#find zombiegames and numShots using collections
			zombieShots = coll.find({"tag":"zombiegame", "meta.eventname" : "shotevent", "meta.levelstate": "boss_mode"}) #, "meta.isballready": True})
		
		#get the count of how many doucments referenced by zombieGames cursor
		numShots[userIndex] = zombieShots.count()

		userIndex = userIndex + 1

	return numShots



'''
Function: Play Duration 

@brief: This function queries the db for each user 
within userList to return the total play duration of a user on the game console

@params: 
- db: the database to query
- userList: a list of users to return play duration's for

@return:
returns a list of the total play durations
'''
def playDuration(db, userList):
	duration = {}	#initialize list to store playDurations
	index = 0	#index variable for returned list of playDurations
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users

	'''Duration of game play for all users in "userList" '''
	#loop through list of users, we are interested in obtaining play duration
	for users in userList:
		#get the current collection of that users
		coll = pymongo.collection.Collection(db, users.lower())

		#get all distinct SON time/date on that certain user -> sort
		userTime = coll.distinct('timestamp')
		
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

		#update index
		index = index + 1

	#returns the list of playDurations for userList
	return duration

''' Zombie vs Space Game '''
def gameDuration(db, userList, gameList):
	#initialize indexing variables and return lists
	zombieIndex = 0
	spaceIndex = 0
	zombieDuration = {}
	spaceDuration = {}
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users

	if gameList: #maybe include later... for passing in game list
		zombieTag = gameList[0]
		spaceTag = gameList[1]

	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		#find zombie and Timestamp using collections and distinct
		zombieGames = coll.find({"tag" : "zombiegame"})
		zombieTime = zombieGames.distinct('timestamp')
		spaceGames = coll.find({"tag" : "endlessgame"})
		spaceTime = list(spaceGames.distinct('timestamp'))

		#check if the user even played zombie game
		if len(zombieTime) > 0: 
			#sort time and get beginning and end
			zombieTime.sort()
			begin = zombieTime[0]
			end = zombieTime[len(zombieTime)-1]

			#calculate duration of game play in hours
			zombieDuration[zombieIndex] = round((end - begin) / 3600, 4)

			#update variables and clear list
			zombieTime[:] = []	
		else:
			zombieDuration[zombieIndex] = 0

		#check if user even played space games
		if len(spaceTime) > 0:
			#sort time and get beginning and end
			spaceTime.sort()
			begin = spaceTime[0]
			end = spaceTime[len(spaceTime)-1]

			#calculate duration of game play in hours
			spaceDuration[spaceIndex] = round((end - begin) / 3600, 4)

			#update variables and clear list
			spaceTime[:] = []
		else:
			spaceDuration[spaceIndex] = 0
		
		#update zombie Index
		zombieIndex = zombieIndex + 1

		#update space index	
		spaceIndex = spaceIndex + 1

	#return both lists of game duration play
	return zombieDuration, spaceDuration

'''Function: priortizeCalc 
for Zombie Game!
@brief: This function will calculate our metric of priortization for a child.
It will calculate the total number of hot zombies that are hit (hotHit) divided 
by the total number of hot zombies (hotTotal).

@params: 
- db: the database to query
- userList: the users to do this for
- mode: mode to analyze -> (normal, boss)
- *****game: the type of game to analyze (could be incorporated for endless game later on)
'''
def prioritizeCalc(db, userList, mode):
	#initialize user index and return lists
	userIndex = 0
	prioritizeList = {}
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users

	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		if mode is "normal":
			#find all the zombie games with normal mode, zombiegothot events
			zombieGames = coll.find({"tag" : "zombiegame", "meta.eventname" : "zombiegothotevent", "meta.levelstate":"normal_mode"})

			#get total number of zombies that got hot
			totalHot = zombieGames.count()
			hotHits = 0

			#get all the distinct zombieID's
			zombieID = list(zombieGames.distinct('meta.zombieid'))

			for ID in zombieID:
				#did zombie get hit?
				zombieHit = coll.find({"tag":"zombiegame", "meta.eventname":"zombiehitevent", "meta.levelstate":"normal_mode", "meta.zombieid":ID})
				#**********????? zombieHit has more than 1 hit count on normal mode?....??????

				if zombieHit.count() > 0:
					hotHits += 1
		
		elif mode is "boss":
			print "add in code for boss"
		
		#update return list to have the priortization 
		if totalHot == 0:
			prioritizeList[userIndex] = 0
		else:
			#convert to float to allow division/disable truncation
			prioritizeList[userIndex] = round(float(hotHits) / totalHot, 4)

		print "prioritize calc. for", users, "hits/total", hotHits, "/", totalHot

		userIndex += 1

	return prioritizeList


''' Function: delibHits
for ZombieGame normal mode right now!
@brief: This function will calculate our metric of how deliberately is a child hitting zombies.
There are three different scenarios: 1) 0 bounces + zombies in LOS, 2) 1 bounces + high SLOS and 3) 1 assist + high helperLOS.
We will look at all the different ball ID's that resulted in successful hits and then back track
to determine how "good" these shots were. 

@params: 
- db: the database to query
- userList: the users to do this for
- mode: mode to analyze -> (normal, boss)
'''
def delibHits(db, userList, mode):
	#initialize user index and return lists
	userIndex = 0
	delibHits = {}
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users

	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())
		#users = {users.lower()}

		isballready = coll.find({"meta.isballready" : True})

		if mode is "normal":
			#find all the ball ids
			balls = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.eventname":"shotevent"})
			ballIDs = balls.distinct('meta.ballid')

			#get total number of zombies shots that were taken
			totalShots = len(ballIDs)

			#get total number of hits
			hits = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.eventname":"zombiehitevent"})
			hitIDs = hits.distinct('meta.ballid')

			#get total number of hits
			totalHits = len(hitIDs)

			#initialize goodhit counter and index
			goodHits = [0]*len(hitIDs)
			hitindex = 0

			goodShots = [0]*(len(ballIDs)-len(hitIDs))
			shotindex = 0

			#sort the lists of ballIDs and hitIDs
			ballIDs.sort()
			hitIDs.sort()

			for ball in ballIDs:
				
				#ball was a hit
				if ball in hitIDs:
					#check if hit was an assist, or less than 2 bounces
					document = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.eventname":"zombiehitevent", "meta.ballid":ball})

					#check if assist
					wasAssist = document.distinct('meta.isassist')
					
					if wasAssist[0] == False:
						checkAssist = False
					else:
						checkAssist = True

					#check if greater than two bounces only if previous was not an assist
					if checkAssist == False:
						wasBounces = document.distinct('meta.ballbounces')
						if wasBounces < 2:
							checkBounce = True
						else:
							checkBounce = False
							#print "check bounce false!!"

					#find the document shotevent for that ball ID
					newdocument = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.eventname":"shotevent","meta.ballid":ball})
					
					#was an assist or less than 2 bounce
					if checkAssist or checkBounce:
						wasHelperLOS = newdocument.distinct('meta.helpersinlos')
						wasHelperSLOS = newdocument.distinct('meta.helpersinslos')
						wasZombieLOS = newdocument.distinct('meta.zombiesinlos')
						wasZombieSLOS = newdocument.distinct('meta.zombiesinslos')

						if wasHelperLOS > 0:
							goodHits[hitindex] = 1
						elif wasHelperSLOS > 0:
							goodHits[hitindex] = 1
						elif wasZombieLOS > 0:
							goodHits[hitindex] = 1
						elif wasZombiesSLOS > 0:
							goodHits[hitindex] = 1
						else:
							goodHits[hitindex] = 0

					hitindex +=1
				
				#ball was not a hit
				else:
					#check if hit was an assist, or less than 2 bounces
					document = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.eventname":"shotevent", "meta.ballid":ball})
					
					#check if the shot had deliberate intentions of hitting something
					wasHelperLOS = document.distinct('meta.helpersinlos')
					wasHelperSLOS = document.distinct('meta.helpersinslos')
					wasZombieLOS = document.distinct('meta.zombiesinlos')
					wasZombieSLOS = document.distinct('meta.zombiesinslos')

					if wasHelperLOS > 0:
						goodShots[shotindex] = 1
					elif wasHelperSLOS > 0:
						goodShots[shotindex] = 1
					elif wasZombieLOS > 0:
						goodShots[shotindex] = 1
					elif wasZombiesSLOS > 0:
						goodShots[shotindex] = 1
					else:
						goodShots[shotindex] = 0

					shotindex += 1

		elif mode is "boss":
			print "add in code for boss"
		
		#update return list to have the priortization 
		if totalShots == 0:
			delibHits[userIndex] = 0	#player didn't even play zombiegame/didn't take shots
		else:
			weightHit = 1
			weightShot = 1

			total = weightHit*sum(goodHits) + weightShot*sum(goodShots)

			#convert to float to allow division/disable truncation
			delibHits[userIndex] = round(float(total) / totalShots, 4)

		print "deliberate calc. for", users, "hits/total", total, "/", totalShots

		userIndex += 1

	return delibHits


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
		#isConnected == True

		#testing the definitions.
		userList = ['adam_bad', 'adam_good']

		zombhits = prioritizeCalc(db, userList, 'normal')
		duration = playDuration(db, userList)
		zombieDuration, spaceDuration = gameDuration(db, userList, 'n/a')
		delibHits = delibHits(db, userList, 'normal')

		print userList
		print zombhits, "prioritization calculation"
		print delibHits, " deliberate hits percentage"
		#print numZomHits, "total number of zombie hits ", numZomHits/numZombShots(db, userList, 'normal')[0], " zombiehits/total shots"