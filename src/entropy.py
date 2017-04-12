import numpy as np

def entropy(table):
    entropy = []

    cols = len(table)
    rows = len(table[0])
    entropy = {}
    
    for j in range(rows):
        row = []
        for i in range(cols):
            row.append(table[i][j])
        entropy[j] = getEntropy(row)
        print"J ", j, " ", row, " => ", entropy[j]
        
    # now get the list index with the highest entropy
    list = [k for k in entropy.keys() if entropy[k] == max(entropy.values())]
    return list




# compute the entropy for a list of
# numerical pos tags
def getEntropy(list, axis=None):
     """Computes the Shannon entropy of the elements of A. Assumes A is
     an array-like of nonnegative ints whose max value is approximately
     the number of unique values present.
     
     (source: http://stackoverflow.com/questions/15450192/fastest-way-to-compute-entropy-in-python)
     """
     if list is None or len(list) < 2:
         return 0.
 
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

