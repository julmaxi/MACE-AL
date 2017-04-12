#! /usr/bin/python

import os, sys
import util
import operator
import numbers
import random
import numpy as np
import math
from collections import defaultdict
from collections import OrderedDict


class Sentences:

    def __init__(self, gfile, tagdict):
        self.dict = defaultdict(list)
        self.mapping = {}
        self.tagdict = tagdict
        self.feedback = defaultdict(list)
        self.processed = {}
        c = 1
        n = 0
        t = 0
        goldlist = util.load_list_from_file(gfile)
        self.feedback[c] = []

        for g in goldlist:
                if g == '\n' or g == '':
                    c += 1
                    t = 0
                    self.feedback[c] = []
                else:
                    wrd, tag = g.split("\t")
                    self.feedback[c].append(None)
                    self.dict[c].append({'w':wrd,'t':tag,'a':[]})
                    self.mapping[n] = {}
                    self.mapping[n]['sid'] = c
                    self.mapping[n]['tid'] = t
                    n += 1
                    t += 1


        
    # take a list of dictionaries for a sentence
    # print it to Stdout and collect the manual
    # annotation for the token at position n
    # store the feedback
        
    def getAnnotation(self, ind, iter):

        sid = self.mapping[ind]['sid']
        tid = self.mapping[ind]['tid']
    
        print iter, ":  "   
        for n in range(len(self.dict[sid])):
            if (tid == n):
                print '\033[1;31m', self.dict[sid][n]['w'], '\033[1;m',
            else:
                print self.dict[sid][n]['w'],
        print
        print
        print "Predicted: ", list(OrderedDict.fromkeys(self.dict[sid][tid]['a'])) 
        print 

        # now read the tag from stdin and return it
        tag = raw_input("Enter tag: ")
       
        # FIXME: fix this so that the first time an unknown tag is entered
        # the system asks whether to add this tag (to prevent typos)
        while (self.checkTag(tag) == False):
            print
            print tag.upper(), " is not a valid tag! Please try again..."
            print
            tag = raw_input("Enter tag: ")
            
        # store feedback
        self.feedback[sid][tid] = tag.upper()
        return tag.upper()

            

    # check if tag is a valid tag from the tagset
    def checkTag(self, tag):
        if (tag.upper() in self.tagdict):
            return True
        else:
            return False
    

    # take a table with predictions (from the annotators/taggers)
    # and add them to the sentences object
    def addPredictions(self, table):
        
        cols = len(table)
        rows = len(table[0])
        sid  = 0
        tid  = 0

        for r in range(rows):            
            # get sid for this row index     
            if (self.mapping[r]['sid'] > sid):
                tid = -1
            sid = self.mapping[r]['sid']
            tid += 1
            for c in range(cols):
                self.dict[sid][tid]['a'].append(table[c][r])
            #print self.dict[sid][tid]

          
                  
    def getSentByInd(self, ind):      
        sid = self.mapping[ind]['sid']
        return self.dict[sid]

    
    def getOracleTag(self, ind):
        sid = self.mapping[ind]['sid']
        tid = self.mapping[ind]['tid']
        tag = self.dict[sid][tid]['t']
        print "get Oracle tag for ", sid, "-", tid, " => ", tag
        self.feedback[sid][tid] = tag
        return tag


    def printSent(self, n):
        for ind in range(len(self.dict[n])):
            print ind, " ", self.dict[n][ind]['w']


    def getGoldTag(n):
        sid = self.mapping[n]['sid']
        tid = self.mapping[n]['tid']
        print sid, "\t", n, "\t", self.dict[sid][tid]['w']

     

    # write feedback file with gold annotations
    # (either from oracle or from goldstandard/AL simulation)    
    # and combine them with predictions from MACE

    def write_feedback_to_file(self, file_path, newAnnotator):
        try:
            file_out = open(file_path,"w")
            for sid in self.dict.keys():
                for row in range(len(self.dict[sid])):
                    if self.feedback[sid][row] == None:
                        file_out.write("\n")
                    else:
                        print "feedback sid ", sid, " row ", row, " => ", self.feedback[sid][row]
                        print "feedback ", str(self.tagdict[self.feedback[sid][row]])
                        file_out.write(str(self.tagdict[self.feedback[sid][row]])+"\n")

            file_out.close()
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)



    def update_predictions(self, newAnnotator):
        for sid in self.dict.keys():
                for row in range(len(self.dict[sid])):
                        # update random classifier    
                        if self.feedback[sid][row] != None:
                            self.dict[sid][row]['a'][newAnnotator] = self.feedback[sid][row]



    def backupFiles(self, c):
        
        # back-up the old preds file
        command = "mv preds.csv preds.csv." + str(c)
        os.system(command)

        # and the feedback file as well        
        command = "cp feedback feedback." + str(c)
        os.system(command)

        # print table content to csv file
        self.printCSV()

        


    # generate csv file, print table to file
    def printCSV(self):
        
        with open('preds.csv', 'w') as csv_file:
            for sid in self.dict.keys():
                for row in range(len(self.dict[sid])):
                    string = ""
                    for pred in range(len(self.dict[sid][row]['a'])):
                        tag = self.dict[sid][row]['a'][pred]
                        if util.number(tag):
                            string + str(tag) + ","
                        else:
                            string += str(self.tagdict[tag]) + ","
                    string = string[:-1]
                    string += '\n'
                    csv_file.write(string)

                    
  
    # take two lists and compute acc.
    def eval_tags(self, gold):
        cols = len(self.dict[1][0]['a'])

        for c in range(cols):
            preds = []
            total = 0
            correct = 0
            for sid in self.dict.keys():
                for tok in range(len(self.dict[sid])):
                    preds.append(self.dict[sid][tok]['a'][c])
            
            # validity check: are the lists of the same length?
            if len(gold) != len(preds):
                print >> sys.stderr, "gold and pred lists are of different length\n"
                print >> sys.stderr, len(gold), " - ", len(pred), "\n"
                sys.exit(1)
        
                    
            for i in range(0, len(gold)):
                if preds[i] != '':
                    if gold[i] == int(self.tagdict[preds[i]]):
                        correct +=1
                    total +=1

            print "Acc: ", float(correct)/total*100, " (", correct, "/", total, ")\n"





    # take two lists and compute acc.
    def majority_baseline(self, gold):
    
        cols = len(self.dict[1][0]['a'])
        correct = 0
        total = 0

        for sid in self.dict.keys():
            for tok in range(len(self.dict[sid])):
                items = self.dict[sid][tok]['a']

                counts = [ (items.count(x), x) for x in set(items) ]
                highest = max(counts)[0]
                candidates = [count[1] for count in counts if count[0] == highest]
                truth = random.choice(candidates)

                # compare vote to gold tag
                if gold[total] == int(self.tagdict[truth]):
                    correct +=1
                total += 1
                
        print "Maj: ", float(correct)/total*100, " (", correct, "/", total, ")\n"


        
        
    # get the n votes with the highest entropy (based on entropy file    
    # generated by MACE) for manual annotation / AL simulation
    def entropy(self, n):
        entropies = util.load_dict_from_file( 'entropies' )
        indices = []
        stop = 0
        for x in sorted(entropies, key=float, reverse=True):
            if entropies[x] in self.processed:
                continue
            indices.append(entropies[x]-1)
            self.processed[entropies[x]] = 1
            stop += 1
            if stop == n:
                return indices
      

        
    # get the n votes with the highest entropy (based on entropy file    
    # generated by MACE) for manual annotation / AL simulation for
    # which the MACE prediction doesn't agree with the majority vote
    def entropyMajority(self, predlist, n):
        entropies = util.load_dict_from_file( 'entropies' )
        indices = []
        stop = 0
        for x in sorted(entropies, key=float, reverse=True):
            if entropies[x] in self.processed:
                continue
            # if prediction == majority vote => continue
            # first, get list of annotations for this index
            items = self.dict[self.mapping[entropies[x]-1]['sid']][self.mapping[entropies[x]-1]['tid']]['a']
            
            # next, get majority vote from the annotations
            counts = [ (items.count(z), z) for z in set(items) ]
            highest = max(counts)[0]
            candidates = [count[1] for count in counts if count[0] == highest]

            # skip if prediction agrees with ??? FIXME!
            # truth = int(self.tagdict[random.choice(candidates)])
            # if truth == predlist[entropies[x]-1]:
            #    continue
                    
            indices.append(entropies[x]-1)
            self.processed[entropies[x]] = 1
            stop += 1
            if stop == n:
                return indices


    # to be used for majority baseline
    # compute entropy based on each row in the annotations
    def get_entropy_for_row(self, N):
        cols = len(self.dict[1][0]['a'])
        entropies = {}
        c = 0
        
        for sid in self.dict.keys():
            for tok in range(len(self.dict[sid])):
                row = self.dict[sid][tok]['a']
                list = [row.count(x) for x in set(row)]
                sum = 0
                for i in list:
                    x = float(i)/float(7)
                    sum += (x * math.log(i))
                entropies[c] = sum
                c += 1

        indices = []
        stop = 0
        for x in sorted(entropies, key=entropies.__getitem__, reverse=False):
                       
            if x in self.processed:
                continue
            indices.append(x)
            self.processed[x] = 1
            stop += 1
            if stop == N:
                return indices
            
 
                    
            

    # compute the entropy for a list of
    # numerical pos tags
    def getEntropy(self, list, axis=None):
        """Computes the Shannon entropy of the elements of A. Assumes A is
        an array-like of nonnegative ints whose max value is approximately
        the number of unique values present.
        
        (from: http://stackoverflow.com/questions/15450192/fastest-way-to-compute-entropy-in-python)
        """
        if list is None or len(list) < 2:
            return 0.
        list = [self.tagdict[x] for x in list]
        
        list = np.asarray(list, dtype=np.int64)
        
        if axis is None:
            list = list.flatten()
            counts = np.bincount(list) # needs small, non-negative ints
            counts = counts[counts > 0]
            if len(counts) == 1:
                return 0. # avoid returning -0.0 to prevent weird doctests
            probs = counts / float(list.size)
            return -np.sum(probs * np.log2(probs))
        elif axis == 0:
            entropies = map(lambda col: entropy(col), list.T)
            return np.array(entropies)
        elif axis == 1:
            entropies = map(lambda row: entropy(row), list)
            return np.array(entropies).reshape((-1, 1))
        else:
            raise ValueError("unsupported axis: {}".format(axis))

