# sample scripts to parse the data directory for the emmersiv games

dataDirPath = "C:\\Users\\Adam\\Desktop\\Data\\"


import os, pymongo, json

conn = None
db = None

testDict = {}

def dumpLinesIntoDatabase(lines):

	countOK = 0
	countDUP = 0
	countFAIL = 0
	total = 0

	for line in lines:
		line = line[line.find("{") : ]
		line = line.replace("ObjectId(" , "").replace(")","")
		jsonObj = json.loads(line)
		total += 1

		
		try:
			_id = db.alldata.insert(jsonObj)
			countOK += 1
		except pymongo.errors.DuplicateKeyError:
			countDUP += 1
		except:
			countFAIL += 1

	return (countOK, countDUP, countFAIL)




if __name__ == '__main__':
	isConnected = False

	# Try to connect with the mongodb server 
	try:
		conn = pymongo.MongoClient()
		db = conn.emmersiv
		print db.collection_names()
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
				



