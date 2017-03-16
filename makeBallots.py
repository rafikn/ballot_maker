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
	file = ''
	candidates = []
	error = False
	test = False
	duplicates = Set()
	missing = Set()
	BLT = list()

	def __init__(self, file, candidates, test):
		self.file = file
		self.candidates = candidates
		self.test = test


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

	def printDiffErrors(self, diff):
		if (test and len(diff) > 0):
			if self.error == False:
				self.error = True

			if len(diff) == 1 and diff[0] < NUM_CANDIDATES:
				print '[ERROR] missing rank %d' % diff[0]
			elif len(diff) == 1 and diff[0] == NUM_CANDIDATES:
				print '[WARN] missing last rank:', diff[0] # 52
			elif len(diff) > 1:
				skipped = all(diff[i+1] - diff[i] == 1 for i in xrange(len(diff)-1))
				if skipped:
					if diff[0] < NUM_CANDIDATES:
						print '[WARN] stopped at rank:', diff[0]
				else:
					for x in diff:
						if x < NUM_CANDIDATES:
							print '[ERROR] missing rank %d' % x
			else:
				print '[ERROR] missing ranks:', diff

	def load(self):
		""" 
			Parse Voting from to BLT 
		"""
		with open(self.file, 'r') as csvfile:
			lines = csv.reader(csvfile)
			index = 0 

			""" 
				lines are formatted as the following:
				Candidate1,Rank1,\s,Candidate2,Rank2
			"""
			votes = {}
			for line in lines:
				if len(line[0]) == 0 or line[0] == 'Candidate':
					continue

				candidate_1 = line[0];
				vote_1 = line[1];
				candidate_2 = line[3];
				vote_2 = line[4];
				if (len(vote_1) > 0):
					if int(vote_1) in votes.keys():
						self.printDuplicated(vote_1)
						
					if int(vote_1) > NUM_CANDIDATES:
						self.printOutOfBound(vote_1)

					votes[int(vote_1)] = candidate_1

				if (len(vote_2) > 0):
					if int(vote_2) in votes.keys():
						self.printDuplicated(vote_1)

					if int(vote_2) > NUM_CANDIDATES:
						self.printOutOfBound(vote_2)


					votes[int(vote_2)] = candidate_2

			diff = list(keys.symmetric_difference(votes.keys()))
			self.printDiffErrors(diff)


			orderedVotes = collections.OrderedDict(sorted(votes.items()))

			self.BLT = list()
			for (vote, candidate) in orderedVotes.items():
				try:
					self.BLT.append(self.candidates[candidate])
				except KeyError, err:
					print '[ERROR]: Cannot find index for candidate %s' % str(err)
					

class BallotMaker:
	""" 
		Transoform a list ranking into a BLT format 
	"""
	candidates = {}
	inverted = {}
	ranking = {}

	forms = list()

	def __init__(self, candidateFile):
		""" 
			Load candidates from file into a dict 
		"""
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
		self.forms = []

		files = glob.glob(path + "/*form.csv")
		if (len(files) == 0):
			print "No forms found in folder:", path
			sys.exit(1)
		else:

			self.forms = list()

			for file in sorted(files):
				if (test):
					print "%s" % file

				form = Form(file, self.candidates, test)
				form.load()

				if (test):
					if (form.error):
						print ''
					else:
						print "OK\n"

				if (invert == False):
					print form.toBLT()

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
						print "[WARN] cadidate '%s' not rankend in '%s'" % (candidate, form.file)
				writer.writerow(ranks)


if __name__ == '__main__':
	usage = """
		Usage:

		makeBallot.py [-p path] [-c candidates] [-t] [-r]

		-p: path to folder containing voting forms
		-c: file containing candidate names
		-t: test voting forms for errors
		-i: invert votes from ballots to candidates

		Parse a voting form (Candidate#1: Rank#1, Candidate#2: Rank#2, etc...) into
		a BLT formatted Ballot : (1 Rank#1 Rank#2 ... 0)
	"""

	# Parse the command line.
	try:
		(opts, args) = getopt.getopt(sys.argv[1:], "p:c:ti")
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
	test = False
	invert = False

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

	if (formsPath == ''):
		print "Specify forms folder";
		print usage
		sys.exit(1)

	if (candidateFile == ''):
		print "Specify candidates file";
		print usage
		sys.exit(1)

	maker = BallotMaker(candidateFile)

	#print maker.candidates
	maker.loadForms(formsPath, test)

	if (invert):
		maker.invert()


