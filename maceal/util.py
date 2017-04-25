#coding:utf-8
import string
from multiprocessing import Process
from random import shuffle
from collections import Counter
import numpy as np
#import json
import re
import os, sys
import operator
import random
import numbers
import math
#from nltk.stem.wordnet import WordNetLemmatizer
#from nltk.corpus import wordnet



def selectSent(table, list):
    print list
    

def get_entropy(row):
    list = [row.count(x) for x in set(row)]
    sum = 0
    for i in list:
        x = float(i)/float(7)
        sum += (x * math.log(i))
    return sum

       
def load_list_from_file(list_file_path):
    list_file = open(list_file_path)
    list = [line.strip() for line in list_file]
    return list


def load_set_from_file(list_file_path):
    list_file = open(list_file_path)
    list = [line.strip() for line in list_file]
    return set(list)


# key : index
def load_dict_from_file(dict_file_path):
    dict = {}
    dict_file = open(dict_file_path)
    lines = [line.strip() for line in dict_file]
    for index, line in enumerate(lines):
        if line == "":
            continue
        dict[line] = index+1
    dict_file.close()
    return dict


# key : index
def load_mapping_from_file(dict_file_path):
    dict = {}
    dict_file = open(dict_file_path)
    for line in dict_file:
        if line == "":
            continue
        ftag, ctag = line.split("\t")
        dict[ftag] = ctag
    dict_file.close()
    return dict


# write dict keys to file
def write_dict_keys_to_file(dict, file_path):
    file_out = open(file_path,"w")
    file_out.write("\n".join([str(key) for key in sorted(dict, key=lambda i: int(dict[i]))]))
    file_out.close()


# read all files in path ending with 'pred'
# append file context to table and return table
def readPredictions( path ):

        files = os.listdir( path )
        ind = 0
        table = []
        filelist = []

        # get all files in path with ending "pred"
        for file in files:
                if file.split(".")[2] =="pred":
                        filelist.append(file)

        # read all files, split the lines and store the tags in table
        for file in filelist:
                file = path + "/" + file
                print "... reading file " + file + " ..."
        
                tags = []
                with open(file) as f:
                        table.append(ind)
                
                        for line in f:
                                if line != '\n':
                                    word, tag = line.split()
                                    tags.append(tag)
                        table[ind] = tags
                        ind+=1
        return table


  

# take two lists and compute acc.
def eval_tags(gold, pred):
    
    # validity check: are the lists of the same length?
    if len(gold) != len(pred):
        print >> sys.stderr, "gold and pred lists are of different length\n"
        print >> sys.stderr, len(gold), " - ", len(pred), "\n"
        sys.exit(1)
        
    total = 0
    correct = 0

    for i in range(0, len(gold)):
        if pred[i] != '':
            if gold[i] == int(pred[i]):
                correct +=1
            total +=1

    string = "ACC: " + str(float(correct)/total*100) + " (" + str(correct) + "/" + str(total) + ")\n"
    print_log(string)


def print_log(string):
    old_stdout = sys.stdout
    logfile = open("log.txt", "a")
    logfile.write(string)
    logfile.close()



def number(x):
    if isinstance(x, numbers.Number):
        return True
    return False

