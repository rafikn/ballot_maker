#!/usr/bin/python

import sys
import getopt
import csv

import os
import glob

import collections

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


	def loadForm(self, form):
		""" 
			Parse Voting from to BLT 
		"""
		with open(form, 'r') as csvfile:
			lines = csv.reader(csvfile)
			index = 0 

			""" 
				lines are formatted as the following:
				Candidate1, Rank1, \s, Candidate2, Rank2
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
					votes[int(vote_1)] = candidate_1
				if (len(vote_2) > 0):
					votes[int(vote_2)] = candidate_2

			orderedVotes = collections.OrderedDict(sorted(votes.items()))

			BLT = '1 '
			for (vote, candidate) in orderedVotes.items():
				try:
					BLT += str(self.candidates[candidate]) + ' '
				except KeyError, err:
					print '[WARN]: Cannot find index for candidate', str(err)
					
			BLT += '0'
			print BLT

	def loadForms(self, path):
		""" 
			Load voting forms from path
		"""
		files = glob.glob(path + "/form_*.csv")
		if (len(files) == 0):
			print "No forms found in folder:", path
			sys.exit(1)
		else:
			for form in files:
				self.loadForm(form)

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

