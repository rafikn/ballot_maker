#!/usr/bin/python

import sys
import getopt
import csv

import os
import glob

import collections
from sets import Set


NUM_CANDIDATES = 52

keys = Set()
for i in range(1, NUM_CANDIDATES + 1):
	keys.add(i)


class Form:

	def __init__(self, file, candidates, stage, test):
		self.file = file
		self.candidates = candidates
		self.votes = {}
		self.duplicates = dict()
		self.missing = Set()
		self.test = test
		self.stage = stage
		self.ranked = 0
		self.error = False
		self.BLT = list()
		self.gaps = 0

	def toBLT(self):
		"""
			Transform votes array into string
		"""
		line = '1 '
		for rank in self.BLT:
			line += str(rank) + ' ' 
					
		line += '0'

		return line


	def printDuplicated(self, vote):
		if self.error == False:
			self.error = True
			self.printErrorFileName('[ERROR] %s' % self.file)
		self.printError('[ERROR] duplicated key %d ' % int(vote))

	def printOutOfBound(self, rank):
		if self.error == False:
			self.error = True
			self.printErrorFileName('[ERROR] %s' % self.file)
		self.printError('[ERROR] rank out of bound  %d ' % int(rank))

	
	def printErrorFileName(self, msg):
		""
		#print msg

	def printError(self, msg):
		if (self.test):
			print msg

	def checkDiff(self, diff):
		if (len(diff) > 0):
			#if self.error == False:
			#	self.error = True

			if len(diff) == 1 and diff[0] <= NUM_CANDIDATES:
				self.missing.add(diff[0])
			elif len(diff) > 1:
				skipped = all(diff[i+1] - diff[i] == 1 for i in xrange(len(diff)-1))
				if skipped:
					if diff[0] < NUM_CANDIDATES:
						""#print '[WARN] stopped at rank:', diff[0]
				else:
					for x in diff:
						if x <= NUM_CANDIDATES:
							self.missing.add(x)


	def updateDuplicates(self, rank, candidate):
		try:
			existing = self.duplicates[rank]
		except KeyError, err:
			existing = list()
			existing.append(self.votes[rank])


		if candidate not in existing:
			existing.append(candidate)

		self.duplicates[rank] = existing


	def addVote(self, vote, candidate):
		if (len(vote) > 0):
			if int(vote) in self.votes.keys():
				self.updateDuplicates(int(vote), candidate)

			if int(vote) > NUM_CANDIDATES:
				self.printOutOfBound(vote)

			self.votes[int(vote)] = candidate
			self.ranked += 1


	def load(self):
		self.duplicates = dict()
		""" 
			Parse Voting from to BLT 
		"""
		with open(self.file, 'rU') as csvfile:
			lines = csv.reader(csvfile)
			index = 0 

			""" 
				lines are formatted as the following:
				Candidate1,Rank1,\s,Candidate2,Rank2
			"""
			for line in lines:
				if len(line[0]) == 0 or line[0].lstrip() == 'Candidate':
					continue

				candidate_1 = line[0].lstrip();
				vote_1 = line[1].lstrip();
				self.addVote(vote_1, candidate_1)

				candidate_2 = line[3].lstrip();
				vote_2 = line[4].lstrip();
				self.addVote(vote_2, candidate_2)


			diff = list(keys.symmetric_difference(self.votes.keys()))
			self.checkDiff(diff)

			orderedVotes = collections.OrderedDict(sorted(self.votes.items()))

			self.BLT = list()
			for (vote, candidate) in orderedVotes.items():
				try:
					self.BLT.append(self.candidates[candidate])
				except KeyError, err:
					print '[ERROR]: Cannot find index for candidate %s' % str(err)


	def checkGaps(self):
		orderedDuplicates= sorted(self.duplicates.keys())
		orderedMissing = sorted(self.missing)

		if (len(orderedDuplicates) > 0):
			firstDuplicate = orderedDuplicates[0]
			self.gaps = 0
			for missing in orderedMissing:
				if  missing < firstDuplicate:
					""" move candidates one rank up"""
					self.gaps += 1


	def truncate(self):
		orderedDuplicates= sorted(self.duplicates.keys())
		orderedMissing = sorted(self.missing)

		if (len(orderedDuplicates) > 0):
			firstDuplicate = orderedDuplicates[0]
			self.gaps = 0
			for missing in orderedMissing:
				if  missing < firstDuplicate:
					""" move candidates one rank up"""
					self.gaps += 1

			self.BLT = self.BLT[:(firstDuplicate- self.gaps - 1)]
			return self

	def breakTies(self, list):
		"""
			Break ties according to an initial list ranking
		"""

					

class BallotMaker:
	""" 
		Transoform a list ranking into a BLT format 
	"""


	def __init__(self, candidateFile, stage):
		""" 
			Load candidates from file into a dict 
		"""
		self.stage = stage
		self.candidates = {}
		self.inverted = {}
		self.ranking = {}
		self.forms = list()

		with open(candidateFile, 'r') as csvfile:
			candidateList = csv.reader(csvfile)
			index = 0 

			for candidate in candidateList:
				index += 1 # BLT ballots are 1-indexed
				self.candidates[candidate[0]] = index

			if (index == 0):
				print 'No candidates present in file:', candidateFile
				sys.exit(1)



	def loadForms(self, path, test):
		""" 
			Load voting forms from path
		"""
		files = glob.glob(path + "/*.csv")
		if (len(files) == 0):
			print "No forms found in folder:", path
			sys.exit(1)
		else:

			self.forms = list()

			for file in sorted(files):
				if (test):
					""
					#print "%s" % file

				#print file

				form = Form(file, self.candidates, self.stage, test)
				form.load()

				self.forms.append(form)



	def invert(self):
		"""
			Invert votes
		"""
		with open('inverted.csv', 'wb') as csvfile:
			writer = csv.writer(csvfile)

			for candidate in self.candidates:
				candidateIndex = self.candidates[candidate]
				
				ranks = list()
				ranks.append(candidate)
				for form in self.forms:
					try:
						ranks.append(form.BLT.index(candidateIndex) + 1)
					except ValueError, err:
						ranks.append(-1)
						print "[WARN] cadidate '%s' not rankend in '%s'" % (candidate, form.file)
				writer.writerow(ranks)


if __name__ == '__main__':
	usage = """
		Usage:

		makeBallot.py [-s stage] [-l list] [-p path] [-c candidates] [-t] [-r]

		-p: path to folder containing voting forms
		-c: file containing candidate names
		-s: stage
			INIT 	(default) initial scaning of the ballots, fix missing ranks, truncate at first duplicate
			FIX 	fix duplicates (requires the list option -l)
		-l: path to a list ranking to use for breaking dupicate ties

		-t: test voting forms for errors
		-i: invert votes from ballots to candidates

		Parse a voting form (Candidate#1: Rank#1, Candidate#2: Rank#2, etc...) into
		a BLT formatted Ballot : (1 Rank#1 Rank#2 ... 0)
	"""

	# Parse the command line.
	try:
		(opts, args) = getopt.getopt(sys.argv[1:], "p:c:s:l:ti")
	except getopt.GetoptError, err:
		print str(err) # will #print something like "option -a not recognized"
		print usage
		sys.exit(1)

	if len(opts) > 4 or len(opts) < 2:
		if len(opts) < 2:
			print "Specify forms folder and candidates file"
			print usage
			sys.exit(1)
		else:
			print "Too many arguments"
			print usage
			sys.exit(1)

	formsPath = ''
	candidateFile = ''
	listPath= ''
	test = False
	invert = False

	stage = "INIT"

	for o, a in opts:
		if o == "-p":
			if (not os.path.isdir(a)):
				print "Path is invalid";
				print usage
				sys.exit(1)
			else:
				formsPath = a
		if o == "-c":
			if (not os.path.exists(a)):
				print "Candidates file is invalid";
				print usage
				sys.exit(1)
			else:
				candidateFile = a
		if o == "-t":
			test = True
		if o == "-i":
			invert = True
		if o == "-l":
			listPath = a
		if o == "-s":
			stage = a

	if (formsPath == ''):
		print "Specify forms folder";
		print usage
		sys.exit(1)

	if (candidateFile == ''):
		print "Specify candidates file";
		print usage
		sys.exit(1)

	maker = BallotMaker(candidateFile, stage)

	#print maker.candidates
	maker.loadForms(formsPath, test)

	if (stage == 'INIT'):
		for form in maker.forms:
			form.truncate()
			print form.toBLT()
	elif (stage == 'FIX'):
		ranked = list()
		with open(listPath, 'rU') as rankedCandidates:
			candidates = csv.reader(rankedCandidates)
			for candidate in candidates:
				ranked.append(candidate[0])

		for form in maker.forms:
			if (form.ranked < 25):
				continue

			line = '1 '
			for c in form.BLT:
				candidate = form.candidates.keys()[form.candidates.values().index(c)]

				duplicate = False
				for tie in form.duplicates.values():
					if candidate in tie:
						duplicate = True

						brokentie = dict()
						for c in tie:
							brokentie[ranked.index(c)] = c

						for rank in sorted(brokentie.keys()):
							candidateAtRank = brokentie[rank]
							line += str(maker.candidates[candidateAtRank]) + ' '


				if not duplicate:
					line += str(c) + ' '

				# line += str(rank) + ' ' 
						
			line += '0'
			print line	

			

					# if (len(range(1, form.gaps + 1)) > 0):
					# 	for gap in range(1, form.gaps + 1):
					# 		adjusted = current + gap
					# 		#dostuff

					# 		if adjusted in form.duplicates.keys():
					# 		#print 'found duplicates', current 
					# 		#print 'candidates tied: ', form.duplicates[current]

					# 			for c in form.duplicates[current]:
					# 				brokentie[ranked.index(c) + 1] = c

					# 			for rank in sorted(brokentie.keys()):
					# 				candidateAtRank = brokentie[rank]
					# 				print candidateAtRank, 'index', maker.candidates[candidateAtRank]

					# 				print current, str(maker.candidates[candidateAtRank])

					# 				line += str(maker.candidates[candidateAtRank]) + ' ' 
					# 				current += 1
					# 		else:
					# 			print current, str(form.BLT[current - 1])
					# 			line += str(form.BLT[current - 1]) + ' ' 

					# 		form.gaps -= 1

					# else:
					# 	#dostuff
					# 	if adjusted in form.duplicates.keys():
					# 		#print 'found duplicates', current 
					# 		#print 'candidates tied: ', form.duplicates[current]

					# 		for c in form.duplicates[current]:
					# 			brokentie[ranked.index(c) + 1] = c

					# 		for rank in sorted(brokentie.keys()):
					# 			candidateAtRank = brokentie[rank]
					# 			print candidateAtRank, 'index', maker.candidates[candidateAtRank]

					# 			print current, str(maker.candidates[candidateAtRank])

					# 			line += str(maker.candidates[candidateAtRank]) + ' ' 
					# 			current += 1
					# 	else:
					# 		print current, str(form.BLT[current - 1])
					# 		line += str(form.BLT[current - 1]) + ' ' 





				
										


					
					# else:
					# 	line += str(rank) + ' ' 


	if (invert):
		maker.invert()