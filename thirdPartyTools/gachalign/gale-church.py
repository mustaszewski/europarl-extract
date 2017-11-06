# -*- coding: utf8 -*-
# Usage:
#  (1) Church-Gale standard parameters for variance and mean:
#      $ python3 gale-church.py st.txt tt.txt
#
#  (2) Automatically calculate parameters for variance and mean from input corpora:
#      $ python3 gale-church.py st.txt tt.txt gacha
#
#  (3) Custom parameters for variance and mean:
#      $ python3 gale-church.py st.txt tt.txt 1.2 4.5
# Source: https://github.com/alvations/gachalign
# Paper: http://www.aclweb.org/anthology/C14-2019
# original code automatically converted from Python2 to Python3 via $ 2to3 -w gale-church.py
# we sentence-aligned them, one paragraph at a time, using a Python implementation (Tan and Bond, 2014) of the standard algorithm of Gale and Church (1993).


"""
An implementation of Gale-Church algorithm with variable mean/variance.

GaChalign-v1.1: Fixed some bugs, compacted the code
Fixed some bugs, now the code runs on command line. 
- removed the evaluation modules, users just want to align their documents.
- simplified gacha to the best configuration (i.e. optimized mean with character).
- removed demo, follow the homepage instructions for usage.
"""

import math, codecs


try:
  import scipy.stats.norm
  norm_logsf = scipy.stats.norm.logsf
except ImportError:
  from minimath import norm_cdf, norm_logsf
    
LOG2 = math.log(2)

BEAD_COSTS = {(1, 1): 0, (2, 1): 230, (1, 2): 230, (0, 1): 450, 
              (1, 0): 450, (2, 2): 440 }

def length_cost(sx, sy, mean_xy, variance_xy):
  """  
  Calculate length cost given 2 sentence. Lower cost = higher prob.
   
  The original Gale-Church (1993:pp. 81) paper considers l2/l1 = 1 hence:
   delta = (l2-l1*c)/math.sqrt(l1*s2)
  
  If l2/l1 != 1 then the following should be considered:
   delta = (l2-l1*c)/math.sqrt((l1+l2*c)/2 * s2)
   substituting c = 1 and c = l2/l1, gives the original cost function.
  """
  lx, ly = sum(sx), sum(sy)
  m = (lx + ly * mean_xy) / 2 
  try:
    delta = (lx - ly * mean_xy) / math.sqrt(m * variance_xy)
  except ZeroDivisionError:
    return float('-inf')
  return - 100 * (LOG2 + norm_logsf(abs(delta)))

def _align(x, y, mean_xy, variance_xy, bead_costs):
  """ 
  The minimization function to choose the sentence pair with 
  cheapest alignment cost. 
  """
  m = {}
  for i in range(len(x) + 1):
    for j in range(len(y) + 1):
      if i == j == 0:
        m[0, 0] = (0, 0, 0)
      else:
        m[i, j] = min((m[i-di, j-dj][0] +
                      length_cost(x[i-di:i], y[j-dj:j], mean_xy, variance_xy) \
                      + bead_cost, di, dj)
                      for (di, dj), bead_cost in BEAD_COSTS.items()
                      if i-di>=0 and j-dj>=0)

  i, j = len(x), len(y)
  while True:
    (c, di, dj) = m[i, j]
    if di == dj == 0:
      break
    yield (i-di, i), (j-dj, j)
    i -= di
    j -= dj
    
def sent_length(sentence):
  """ Returns sentence length without spaces. """
  return sum(1 for c in sentence if c != ' ')

def align(sx, sy, mean_xy, variance_xy, bc):
  """ Main alignment function. """
  cx = list(map(sent_length,sx)); cy = list(map(sent_length, sy)) 
  for (i1, i2), (j1, j2) in \
  reversed(list(_align(cx, cy, mean_xy, variance_xy, bc))):
    yield ' '.join(sx[i1:i2]), ' '.join(sy[j1:j2])
    
def readFile(filename):
  """ Yields sections off textfiles delimited by '#'. """
  paragraph = []; doc = ""
  for line in codecs.open(filename, "r","utf8"):
    if line.strip() == "<P>" or line[0] == "<P>":
      if paragraph != [] and doc != "":
        yield paragraph, doc
        paragraph = []
      doc = line.strip() #line.strip().rpartition('/')[-1]
    else:
      paragraph.append(line.strip())

def calculateMean(srcfile, trgfile):
  """ Caluclate mean length: mean = len(trgfile) / len(srcfile). """
  srcfile = codecs.open(srcfile,'r','utf8').read().replace(" ","")
  trgfile = codecs.open(trgfile,'r','utf8').read().replace(" ","")
  return len(trgfile)/float(len(srcfile))


def calculateVariance(srcfile,trgfile):
  """ Calculates covariance between len(srcfile) and len(trgfile). """
  try:
    from pylab import polyfit
  except ImportError:
    import os
    os.system('sudo pip install -U --force-reinstall scipy')
  diffsquares = [math.pow(len("".join(src[0]).replace(" ","")) \
                          - len("".join(trg[0]).replace(" ","")),2) \
                for src, trg in zip(readFile(srcfile),readFile(trgfile))]
  src_paragraph_len = [len(i[0]) for i in readFile(srcfile)]
  (m,_)= polyfit(src_paragraph_len,diffsquares,1)
  return m


def main(corpusx, corpusy, mean=1.0, variance=6.8, bc = BEAD_COSTS):
  if mean == "gacha":
    mean = calculateMean(corpusx, corpusy)
  mean, variance = list(map(float,[mean,variance]))
  # Show Users the mean/variance.
  msg = " ".join(["Aligning corpus with mean =", str(mean), 
                    "and variance = ", str(variance), '\n'])
  sys.stderr.write(msg)
  for src,trg in zip(readFile(corpusx),readFile(corpusy)):
    #assert src[1] == trg[1] # This statement ensures that each block needs to have the same title after a # across ST and TT # remove this
    print(src[1])
    for (sentence_x, sentence_y) in align(src[0], trg[0], mean, variance, bc):
      print(sentence_x + "~~\t~~" + sentence_y)

if __name__ == '__main__':
  import sys
  if len(sys.argv) not in list(range(3,6)):
    sys.stderr.write('Usage: %srcfile corpus.x corpus.y '
                     '(mean) (variance) (bead_costs)\n' % sys.argv[0])
    sys.exit(1)
  main(*sys.argv[1:])
