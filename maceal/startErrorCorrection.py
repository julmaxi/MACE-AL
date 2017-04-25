#!/usr/bin/python

import os, sys
import util
import pprint
import random
from optparse import OptionParser
from maceal.sentences import Sentences


# eval individual taggers/annotators against gold standard
# and also the best prediction made by MACE
def evalTagger(goldfile, sentences):

        #FIXME we now should have a GoldSent object here
        gold = readGold(goldfile, sentences)
        
        # evaluate each tagger against the goldstandard
        sentences.eval_tags(gold)

        # and also add the results for a majority vote
        sentences.majority_baseline(gold)
                

        
# now evaluate the best prediction by MACE against gold
def evalPredictions(goldfile, predlist, sentences):

        #FIXME we now should have a GoldSent object here
        gold = readGold(goldfile, sentences)
        util.eval_tags(gold, predlist) # FIXME! moved to sentences with different args
                                       # so maybe we keep it here... slightly redundant, but...


        
# read the goldstandard file and return it as a list
# convert tags to numerical format
def readGold(gold, sentences):
        
        goldlist = []
        sentdict = {}

        # read gold file
        gold = util.load_list_from_file(gold)
        for line in gold:
                if line != '\n' and line != '':
                        word, tag = line.split('\t')
                        # new, unknown tag? add to dictionary
                        if tag not in sentences.tagdict:
                                newTag = len(sentences.tagdict) +1
                                sentences.tagdict[tag] = newTag
                                util.write_dict_keys_to_file(sentences.tagdict, './dict/tags.txt')
                        goldlist.append(sentences.tagdict[tag])
        return goldlist


                        
# convert table content to numerical representation
# e.g. CC = 8, CD = 9, ...
def convert2num(table, sentences):
        for x in range(0, len(table)):
                for y in range(0, len(table[x])):
                        table[x][y] = sentences.tagdict[table[x][y]]
        return table




# read the MACE competence file and return the index
# for the annotator with the lowest competence
def getLowestCompetence(comp_file_path):
    list = util.load_list_from_file(comp_file_path)
    lowest = 1
    index = -1
    for i, val in enumerate(list[0].split("\t")):
        if (max(float(val),lowest) == lowest):
            lowest = float(val)
            index = i            
    return index


# take the index of the annotator with the lowest competence
# (according to the model) and replace its predictions with
# the ones predicted by MACE
def replaceLowestCompetenceByMACEpred(lowest, table, predlist, c):

        for x in range(0, len(table[lowest])):
                table[lowest][x] = predlist[x]
            
        # back-up the old preds file
        command = "mv preds.csv preds.csv." + str(c)
        os.system(command)

        # now generate the new csv file, print table to file
        # and run next iteration with the new predictions
        sentences.printCSV()



def run_iteration(options, sentences, table, c):
        #####
        # create new annotator from best predictions and get N tags for the predictions with
        # the highest entropy and update the new annotator (feedback from oracle)
        # either replace a random annotator in every round
        bad_guy = random.choice(range(len(table)))
        
        # or replace the one with the lowest competence (don't! doesn't work well...)
        if options.lowest:
                bad_guy = getLowestCompetence('./competence')
                replaceLowestCompetenceByMACEpred(bad_guy, table, predlist, c)
                # print "Replace annotator ", bad_guy
        
        # select table entry with highest entropy
        # returns a list with row indices for the rows
        # in the table that have the highest entropy (from file "entropy" created by MACE)
        N = 1
        indices = sentences.entropy(N) 
        #### don't use: indices = sentences.entropyMajority(predlist, N)
        #indi = sentences.get_entropy_for_row(N)
        print "ENTROPY:  ", indices
        #print "MAJORITY: ", indi
        print
        for ind in indices:
                print "Option: ", options.simulation
                if options.simulation:
                        print "run simulation........................."
                        # either from the gold standard (AL simulation)
                        tag = sentences.getOracleTag(ind)
                else:
                        print "ask oracle............................."
                        # or from the oracle (real AL)
                        tag = sentences.getAnnotation(ind, c)

                util.print_log("TAG: " + tag.upper() + "\n")

        
        # now use oracle tags as feedback, combined with the predlist features from MACE
        # create control file and rerun EM
        if options.feedback:
            sentences.write_feedback_to_file(options.feedback, bad_guy)
        sentences.update_predictions(bad_guy)
        sentences.backupFiles(c)
        
        # read updated predictions from file (with feedback from oracle/AL simulation)
        #table = util.readPredictions(options.path)
        
        # convert tags to numerical representation
        #table = convert2num(table, tagdict)

        # run MACE
        if options.entropies:
                if options.feedback:
                        command = "java -jar ./MACE.jar --controls feedback --entropies preds.csv"
                else:
                        command = "java -jar ./MACE.jar --entropies preds.csv"
        else:
                if options.feedback: 
                        command = "java -jar ./MACE.jar --controls feedback preds.csv"
                else:
                        command = "java -jar ./MACE.jar preds.csv"
        if options.restarts:
                newarg = "MACE.jar --restarts " + options.restarts
                command = command.replace("MACE.jar", newarg)
        if options.vanilla:
            newarg = "MACE.jar --em "
            command = command.replace("MACE.jar", newarg)

        os.system(command)

        # read MACE predictions
        predlist = util.load_list_from_file('prediction')

        # if we have a gold file, evaluate best predictions against gold
        if options.goldstandard != False:
            evalTagger(options.goldstandard, sentences) 
            evalPredictions(options.goldstandard, predlist, sentences)



###########################################################################
###
###   main
###
###########################################################################

        

def run_cmd_interface():
        # parse command line options
        optparser = OptionParser()
        optparser.add_option("-p", "--predfile", dest="path", 
                             default="../data/output", 
                             help="path to dir with predictions", metavar="DIR")
        optparser.add_option("-g", "--gold", dest="goldstandard", default=False,
                             help="read gold standard annotations (optional)")
        optparser.add_option("-f", "--feedback", dest="feedback", default=False,
                             help="read feedback from oracle annotations (optional)")
        optparser.add_option("-e", "--entropies", dest="entropies", default=False,
                             help="print entropies for each instance to file (MACE)")
        optparser.add_option("-m", "--majority", dest="majority", default=False,
                             help="instead of posterior entropies, use majority vote")
        optparser.add_option("-r", "--restarts", dest="restarts", default=False,
                             help="number of random model initialisations")
        optparser.add_option("-s", "--simulation", dest="simulation", default=False,
                             help="run program as AL simulation")
        optparser.add_option("-v", "--vanilla", dest="vanilla", default=False,
                            help="run program with vanilla EM")
        optparser.add_option("-l", "--lowest", dest="lowest", default=False,
                             help="replace annotator with the lowest competence")

        (options, args) = optparser.parse_args()

        
        tagdict = util.load_dict_from_file('./dict/tags.txt')
        mapping = util.load_mapping_from_file('./dict/mapping.txt')
                
        # read gold standard (or, if no gold annotations exist, list with word tokens)
        sentences = Sentences(options.goldstandard, tagdict)

        # read predictions from file
        table = util.readPredictions(options.path)
        
        # add predictions
        sentences.addPredictions(table)
        
        # convert tags to numerical representation
        table = convert2num(table, sentences)

        # print table content to csv file
        sentences.printCSV()
     

        # and update table with existing predictions from experiment (preds.csv)

        # run MACE
        if options.entropies:
                command = "java -jar ./MACE.jar --entropies preds.csv"
        else:
                command = "java -jar ./MACE.jar preds.csv"
        if options.restarts:
                newarg = "MACE.jar --restarts " + options.restarts
                command = command.replace("MACE.jar", newarg)
        if options.vanilla:
                newarg = "MACE.jar --em "
                command = command.replace("MACE.jar", newarg)


        os.system(command)
        
        
        # read MACE predictions
        predlist = util.load_list_from_file('prediction')

        # if we have a gold file, evaluate best predictions against gold
        if options.goldstandard != False:
                evalTagger(options.goldstandard, sentences) 
                evalPredictions(options.goldstandard, predlist, sentences)
        
        # FIXME: the max range should also be a parameter (right now the number of iterations is hard-coded)       
        # also, it should be able to end/continue with the annotation at every point in time...
        for c in range(0, 500):
            run_iteration(options, sentences, table, c)
