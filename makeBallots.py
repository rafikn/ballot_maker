#!/usr/bin/python

import sys
import getopt
import csv

import os
import glob

import collections
from sets import Set

keys = Set()
for i in range(1, 53):
	keys.add(i)


class Form:
	file = ''
	candidates = []
	error = False
	duplicates = Set()
	missing = Set()

	def __init__(self, file, candidates):
		self.file = file
		self.candidates = candidates

	def load(self):
		""" 
			Parse Voting from to BLT 
		"""
		with open(self.file, 'r') as csvfile:
			lines = csv.reader(csvfile)
			index = 0 
			error = False
			""" 
				lines are formatted as the following:
				Candidate1,Rank1,\s,Candidate2,Rank2
			"""
			votes = {}
			for line in lines:

				if len(line[0]) == 0 or line[0] == 'Candidate':
					continue

				candidate_1 = line[0]
				vote_1 = line[1]
				candidate_2 = line[3]
				vote_2 = line[4]

				if (len(vote_1) > 0):
					if int(vote_1) in votes.keys():
						if error == False:
							error = True
							print '[ERROR]', self.file
						print '[ERROR] duplicated key', int(vote_1)

					if int(vote_1) > 52:
						if error == False:
							error = True
							print '[ERROR]', self.file
						print '[ERROR] rank out of bounds', vote_1

					votes[int(vote_1)] = candidate_1

				if (len(vote_2) > 0):
					if int(vote_2) in votes.keys():
						if error == False:
							error = True
							print '[ERROR]', self.file
						print '[ERROR] duplicated key', int(vote_2)
					if int(vote_2) > 52:
						if error == False:
							error = True
							print '[ERROR]', self.file
						print '[ERROR] rank out of bounds', vote_2

					votes[int(vote_2)] = candidate_2

			diff = list(keys.symmetric_difference(votes.keys()))
			if (len(diff) > 0):
				if len(diff) == 1 and diff[0] < 52:
					print '[ERROR] missing rank %d' % diff[0]
				elif len(diff) == 1 and diff[0] == 52:
					print '[WARN] stopped at rank:', diff[0] # 52
				elif len(diff) > 1:
					skipped = all(diff[i+1] - diff[i] == 1 for i in xrange(len(diff)-1))
					if skipped:
						if diff[0] <= 52:
							print '[WARN] stopped at rank:', diff[0]
					else:
						for x in diff:
							if x < 52:
								print '[ERROR] missing rank %d' % x

			# 	else:
			# 		print '[ERROR] missing ranks:', diff


			orderedVotes = collections.OrderedDict(sorted(votes.items()))

			BLT = '1 '
			for (vote, candidate) in orderedVotes.items():
				try:
					BLT += str(self.candidates[candidate]) + ' '
				except KeyError, err:
					if error == False:
						error = True
						print '[ERROR]', self.file
						print '[ERROR]: Cannot find index for candidate', str(err)
					
			BLT += '0'
			if error == False:
				print '[INFO]', self.file, 'OK'
			# 	print BLT
			print ''

class BallotMaker:
	""" Transoform a list ranking into a BLT format """
	candidates = {}
	ranking = {}

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

			print "Loaded", index, "candidates"

		

	def loadForms(self, path):
		""" 
			Load voting forms from path
		"""
		files = glob.glob(path + "/form_*.csv")
		if (len(files) == 0):
			print "No forms found in folder:", path
			sys.exit(1)
		else:
			for file in sorted(files):
				form = Form(file, self.candidates)
				form.load()


if __name__ == '__main__':
	usage = """
		Usage:

		makeBallot.py [-p path] [-c candidates]

		-p: path to folder containing voting forms
		-c: file containing candidate names

		Parse a voting form (Candidate#1: Rank#1, Candidate#2: Rank#2, etc...) into
		a BLT formatted Ballot : (1 Rank#1 Rank#2 ... 0)
	"""

	# Parse the command line.
	try:
		(opts, args) = getopt.getopt(sys.argv[1:], "p:c:")
	except getopt.GetoptError, err:
		print str(err) # will print something like "option -a not recognized"
		print usage
		sys.exit(1)

	if len(opts) != 2:
		if len(opts) < 2:
			print "Specify forms folder and candidates file"
		else:
			print "Too many arguments"
			print usage
			sys.exit(1)

	formsPath = ''
	candidateFile = ''

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


	maker = BallotMaker(candidateFile)
	maker.loadForms(formsPath)

