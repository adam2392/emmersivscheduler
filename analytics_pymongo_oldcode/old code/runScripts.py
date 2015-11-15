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
import os, pymongo, json, csv, time
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
	if len(numShots) == 1:
		numShots = numShots[0]

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
	
	if len(duration) == 1:
		duration = duration[0]

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

	if len(zombieDuration) == 1:
		zombieDuration = zombieDuration[0]
	if len(spaceDuration) == 1:
		zombieDuration = zombieDuration[0]
		
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
			zombieGames = coll.find({"tag" : "zombiegame", "meta.eventname" : "zombiegothotevent", "meta.levelstate":"normal_mode", "meta.sublevelstate":"zombies"})

			#get total number of zombies that got hot
			totalHot = zombieGames.count()
			hotHits = 0

			#get all the distinct zombieID's
			zombieID = list(zombieGames.distinct('meta.zombieid'))

			for ID in zombieID:
				#did zombie get hit?
				zombieHit = coll.find({"tag":"zombiegame", "meta.eventname":"zombiehitevent", "meta.levelstate":"normal_mode", "meta.sublevelstate":"zombies", "meta.zombieid":ID})
				#**********????? zombieHit has more than 1 hit count on normal mode?....??????

				if zombieHit.count() > 0:
					hotHits += 1
		
			#update return list to have the priortization 
			if totalHot == 0:
				prioritizeList[userIndex] = 0
			else:
				#convert to float to allow division/disable truncation
				prioritizeList[userIndex] = round(float(hotHits) / totalHot, 4)
		
		elif mode is "boss":
			''' find good shots towards boss and penalize shots at zombies w/ FF and bad shots '''
			#find the boss
			# boss = coll.find({"tag" : "zombiegame", "meta.isboss" : True, "meta.levelstate":"boss_mode"})
			# bossID = boss.distinct('meta.zombieid')

			#find all the ball ids
			# balls = coll.find({"tag":"zombiegame", "meta.levelstate":"boss_mode", "meta.eventname":"shotevent"})
			# ballIDs = balls.distinct('meta.ballid')
			# totalShots = len(ballIDs)
			totalShots = numZombShots(db, users, 'boss')

			#find all the good hits on the boss
			goodhits = coll.find({"tag":"zombiegame", "meta.levelstate":"boss_mode", 
								"meta.eventname":"zombiehitevent", "meta.isboss" : True, "meta.ballbounces" : {"$lt" : 2}})
			goodhitIDs = goodhits.distinct('meta.ballid')

			#find all the good "shots" on boss
			goodshots = coll.find({"tag":"zombiegame", "meta.levelstate":"boss_mode", 
								"meta.eventname":"shotevent", "meta.isbossinrange" : True})
			goodshotIDs = goodshots.distinct('meta.ballid')
			goodshotIDs = [x for x in goodshotIDs if x not in goodhitIDs]

			#penalize hits that hit FF zombies and "isbossinrange":False
			hitIDs = coll.find({"tag":"zombiegame", "meta.levelstate":"boss_mode", 
				"meta.eventname":"zombiehitevent", "meta.isboss":False, "meta.isdead":False})
			penaltyCount = float(len(hitIDs.distinct('meta.ballid')))
			
			#get the total good count
			totalGood = float(len(goodhitIDs) + len(goodshotIDs))/totalShots

			#get total penalty
			totalPenalty = float(penaltyCount)/totalShots

			# print totalGood, "totalgood"
			# print totalGood, totalPenalty, "totalgood, penalty count"
			
			#set up return prioritizeList
			if totalShots == 0:
				prioritizeList[userIndex] = 0
			else:
				prioritizeList[userIndex] = round(totalGood, 4)

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

@returns:
-delibHits : # of deliberate hits taken per user
-delibShots : # of deliberate shots taken per user
'''
def delibHitsAndShots(db, userList, mode):
	#initialize user index and return lists
	userIndex = 0
	delibHits = {}
	delibShots = {}
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users

	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())
		#users = {users.lower()}

		isballready = coll.find({"meta.isballready" : True})

		if mode is "normal":
			#find all the ball ids
			balls = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.sublevelstate":"zombies", "meta.eventname":"shotevent"})
			ballIDs = balls.distinct('meta.ballid')

			#get total number of zombies shots that were taken
			totalShots = len(ballIDs)

			#get total number of hits
			hits = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.sublevelstate":"zombies", "meta.eventname":"zombiehitevent"})
			hitIDs = hits.distinct('meta.ballid')

			#get total number of hits
			totalHits = len(hitIDs)

			#initialize goodhit counter and index
			goodHits = [0]*len(hitIDs)
			hitindex = 0

			#initialize goodshots counter and index
			goodShots = [0]*(len(ballIDs)-len(hitIDs))
			shotindex = 0

			#loop through each ballID
			for ball in ballIDs:
				
				#ball was a hit
				if ball in hitIDs:
					#check if hit was an assist, or less than 2 bounces
					document = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.sublevelstate":"zombies", "meta.eventname":"zombiehitevent", "meta.ballid":ball})

					#check if assist
					wasAssist = document.distinct('meta.isassist')
					
					#find the document shotevent for that ball ID
					newdocument = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.sublevelstate":"zombies", "meta.eventname":"shotevent","meta.ballid":ball})
					addHit = 1

					if wasAssist[0] == True:					
						#count number of helpers in LOS/SLOS
						wasHelperLOS = newdocument.distinct('meta.helpersinlos')
						wasHelperSLOS = newdocument.distinct('meta.helpersinslos')

						#if it was an assist, and helpers were in sight
						if wasHelperLOS > 0 or wasHelperSLOS > 0:
							addHit = 1
						else:
							addHit = 0
					
					#now check bounces if previous statement did not result in a false hit
					if addHit != 0:
						wasBounces = document.distinct('meta.ballbounces')
						
						#bounced once, or zero times
						if sum(wasBounces) < 2:
							checkBounce = True
						
							#count number of zombies in LOS/SLOS
							wasZombieLOS = newdocument.distinct('meta.zombiesinlos')
							wasZombieSLOS = newdocument.distinct('meta.zombiesinslos')

							if (wasZombieLOS > 0 or wasZombieSLOS > 0):
								addHit = 1
							else:
								addHit = 0
						
						#if it was a hit w/ more than 2 bounces
						else:
							checkBounce = False
							addHit = 0
							#print "check bounce false!!"
						
					#Add this ballID to a "goodHit" if conditions are satisfied						
					if addHit == 1:
						goodHits[hitindex] = 1
					else:
						goodHits[hitindex] = 0

					hitindex +=1
				
				#ball was not a hit
				else:
					document = coll.find({"tag":"zombiegame", "meta.levelstate":"normal_mode", "meta.sublevelstate":"zombies", "meta.eventname":"shotevent", "meta.ballid":ball})
					
					#check if the shot had deliberate intentions of hitting something
					wasHelperLOS = document.distinct('meta.helpersinlos')
					wasHelperSLOS = document.distinct('meta.helpersinslos')
					wasZombieLOS = document.distinct('meta.zombiesinlos')
					wasZombieSLOS = document.distinct('meta.zombiesinslos')

					#go through each and check if there was something in the LOS -> good shot
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

		'''Set up the return lists to hold the number of deliberate hits and shots per user'''
		#no shots fired
		if totalShots == 0:
			delibHits[userIndex] = 0	#player didn't even play zombiegame/didn't take shots
			delibShots[userIndex] = 0
		
		#shots were fired
		else:
			#assign the goodHits, and goodShots to return lists
			delibHits[userIndex] = sum(goodHits)
			delibShots[userIndex] = sum(goodShots)

		userIndex += 1

	return delibHits, delibShots

'''Calculate deliberate attempts '''
def delibCalc(delibHits, delibShots, totalShots, weightHit, weightShot):
	delibAttempts = {}
	index = 0

	#if passed in value was only a single value, convert to a list for looping
	if isinstance(delibHits, basestring):
		delibHits = {delibHits}	
	if isinstance(delibShots, basestring):
		delibShots = {delibShots}
	if isinstance(totalShots, basestring):
		totalShots = {totalShots}	

	maxWeight = weightHit if weightHit > weightShot else weightShot

	for index in xrange(0, len(delibHits)):
		total = weightHit*delibHits[index] + weightShot*delibShots[index]

		#do calculation and normalize it
		delibAttempts[index] = (round(float(total) / totalShots[index], 4))/maxWeight

	#if only a single entry, return as a single value, else return as a list
	if len(delibAttempts) == 1:
		delibAttempts = delibAttempts[0]

	return delibAttempts

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
		userList = ['adam_bad', 'adam_good']
		weightHit = 2
		weightShot = 2

		# duration = playDuration(db, userList)
		zombieDuration, spaceDuration = gameDuration(db, userList, 'n/a')

		totalShots = numZombShots(db, userList, 'normal')
		prioritizehitsnormal = prioritizeCalc(db, userList, 'normal')
		prioritizehitsboss = prioritizeCalc(db, userList, 'boss')
		delibHits, delibShots = delibHitsAndShots(db, userList, 'normal')
		
		delibAttempts = delibCalc(delibHits, delibShots, totalShots, weightHit, weightShot)

		print userList, "weightHit: ", weightHit, "weightShot: ", weightShot
		print zombieDuration, "zombie play duration (hrs)"
		print prioritizehitsnormal, "prioritization normal calculation"
		print prioritizehitsboss, "prioritization boss calculation"
		print delibAttempts, " deliberate hits percentage"
		#print numZomHits, "total number of zombie hits ", numZomHits/numZombShots(db, userList, 'normal')[0], " zombiehits/total shots"
'''
		with open('testdata.csv', 'w') as csvfile:
			#gets the current date and time to write into header row
			date = time.strftime("%d/%m/%Y")
			datewrite = 'Testing good vs bad for: {!s}'.format(date)

			#create header writer object
			writer = csv.DictWriter(csvfile, fieldnames = [datewrite, 'User', 'prioritization %','deliberate hit %', 
				'good_hits', 'good_shots', 'total_good (after weight)', 'total_shots'], lineterminator='\n')
			writer.writeheader()

			#create data writer object for testing data
			testwriter = csv.writer(csvfile, delimiter = ',', lineterminator='\n')

			data = [['', userList[0], prioritizehits[0], delibHits[0], 'ghits', 'gshots', 'tgood', 'tshots'],
					['', userList[1], prioritizehits[1], delibHits[1], 'ghits', 'gshots', 'tgood', 'tshots']]
			
			weights = [['','Hit_Weight', 'Shot_Weight'],
						['','weight_hit', 'weight_shot']]

			testwriter.writerows(data)
			testwriter.writerows(weights)	
'''	