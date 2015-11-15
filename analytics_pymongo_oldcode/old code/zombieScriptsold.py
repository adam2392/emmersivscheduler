
''' find number of zombies hit '''
def numZombHits(db, userList, mode):
	#initialize indexing variables and return lists
	userIndex = 0
	numHits = {}
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users
		
	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())

		#find zombiegames and numShots using collections
		zombieGames = coll.find({"tag":"zombiegame", "meta.eventname" : "zombiehitevent", "meta.levelstate":mode})
		
		#get the count of how many doucments referenced by zombieGames cursor
		numHits[userIndex] = zombieGames.count()

		userIndex = userIndex + 1
	return numHits


''' get the number of times zombies got hot event (close to the user)'''
def zombHot(db, userList):
	userIndex = 0
	countHot = {}
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users

	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())
		print "currently looking at ", users.lower(), "to count number of times got HOT"

		zombieHot = coll.find({"tag":"zombiegame", "meta.eventname":"zombiegothotevent"})

		countHot[userIndex] = zombieHot.count()

		userIndex = userIndex + 1

	return countHot

''' Find number of hot zombies that got hit '''
def hotZombHits(db, userList):
	userIndex = 0
	numHits = {}
	total = 0
	if isinstance(userList, basestring):
		userList = {userList}	#converts into a list, to handle case of only passing in 1 user, or multiple users

	#loop through userlist
	for users in userList:
		coll = pymongo.collection.Collection(db, users.lower())
		print "currently looking at ", users.lower(), " to count number of hot zombies hit"

		#find all cursors of zombiegame and gothot event
		zombieHot = coll.find({"tag":"zombiegame", "meta.eventname": "zombiegothotevent"})

		#find all the distinct id's
		zombieHotIds = zombieHot.distinct('meta.zombieid')
		
		zombieHotIds.sort()
		print zombieHotIds
		
		#loop through the zombieHotIds to see if there was a hit event
		for ID in zombieHotIds:
			zombieHit = coll.find({"tag":"zombiegame", "meta.eventname": "zombiehitevent", "meta.zombieid": ID})

			#***************Test *************
			testnumber = zombieHit.count()
			print testnumber, "for ID: ", ID

			total += testnumber

		numHits[userIndex] = total
		#update user index
		userIndex += 1
		total = 0

	return numHits
