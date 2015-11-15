#!/usr/bin/env python

# obstacle = {}

# test = {1, 2, 3, 4}
userList = {'a', 'b', 'c'}

# obstacle[0] = test
# obstacle[1] = testv

# print obstacle[0]


# #return list of coins count
redCoins = {}
blueCoins = {}
yellowCoins = {}
deathSets = {}
red = {}
blue = {}
yellow = {}

userIndex = 0
for users in userList:
	
	deathSets[userIndex] = {'adam', 'l1', 'b2', 'b4'}
	index = 0
	# red.clear()
	# blue.clear()
	# yellow.clear()

	#use obstaclecoin count to check # coins in that death obstacle
	for death in deathSets[userIndex]:
		if index is 3:
			red[index] = 400
			blue[index] = 500
			yellow[index] = 600
		else:
			red[index] = 100
			blue[index] = 700
			yellow[index] = 900
		index += 1

	redCoins[userIndex] = red
	blueCoins[userIndex] = blue
	yellowCoins[userIndex] = yellow
	userIndex += 1

print yellowCoins[0][3]
print redCoins
print blueCoins
print yellowCoins