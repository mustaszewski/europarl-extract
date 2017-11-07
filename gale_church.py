# -*- coding: utf8 -*-

"""
An implementation of Gale-Church algorithm with variable mean/variance.

GaChalign-v1.1: Fixed some bugs, compacted the code
Fixed some bugs, now the code runs on command line. 
- removed the evaluation modules, users just want to align their documents.
- simplified gacha to the best configuration (i.e. optimized mean with character).
- removed demo, follow the homepage instructions for usage.

Original version by
Tan, Liling & Bond, Francis (2014): NTU-MC Toolkit: Annotating a Linguistically Diverse Corpus. In: 
Proceedings of COLING 2014: System Demonstrations, 86-89 (http://www.aclweb.org/anthology/C14-2019).
Source code available at https://code.google.com/archive/p/gachalign/downloads

Original code customized for implementation with EuroParlExtract by Michael Ustaszewski (2017).
}
"""

import math, codecs

LOG2 = math.log(2)

BEAD_COSTS = {(1, 1): 0, (2, 1): 230, (1, 2): 230, (0, 1): 450, 
              (1, 0): 450, (2, 2): 440 }

def norm_cdf(z):
  """ Just in case you haven't installed scipy, use the norm distribution 
  functions as of Gale-Church'srcfile (1993). """
  # Equation 26.2.17 from Abramowitz and Stegun (1964:p.932)
  
  t = 1/float(1+0.2316419*z) # t = 1/(1+pz) , z=0.2316419
  probdist = 1 - 0.3989423*math.exp(-z*z/2) * ((0.319381530 * t)+ \
                                         (-0.356563782* math.pow(t,2))+ \
                                         (1.781477937 * math.pow(t,3)) + \
                                         (-1.821255978* math.pow(t,4)) + \
                                         (1.330274429 * math.pow(t,5)))
  return probdist


def norm_logsf(z):
  """ Take log of the survival fucntion for normal distribution. """
  try:
    return math.log(1 - norm_cdf(z))
  except ValueError:
    return float('-inf')


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

  
def readSentences(sentencelist):
  """ Yields sections off textfiles delimited by '<P>'. """
  paragraph = []; doc = ""
  for sent in sentencelist:
    
  #for line in codecs.open(filename, "r","utf8"):
    if sent.strip() == "<P>" or sent[0] == "<P>":
      if paragraph != [] and doc != "":
        yield paragraph, doc
        paragraph = []
      doc = sent.strip() #line.strip().rpartition('/')[-1]
    else:
      paragraph.append(sent.strip())

def calculateMean(sl_sentences, tl_sentences):
  """ Caluclate mean length: mean = len(trgfile) / len(srcfile). """
  #srcfile = codecs.open(srcfile,'r','utf8').read().replace(" ","")
  srcfile = "".join(sl_sentences).replace(" ", "")
  #print("\")
  trgfile = "".join(tl_sentences).replace(" ", "")
  x = len(trgfile)
  y = len(srcfile)
  #trgfile = codecs.open(trgfile,'r','utf8').read().replace(" ","")
  print("   Mean is %s / %s " %(x, y))
  return len(trgfile)/float(len(srcfile))

'''
def calculateVariance(srcfile,trgfile):
  """ Calculates covariance between len(srcfile) and len(trgfile). """
  try:
    from pylab import polyfit # Requires pylab...
  except ImportError:
    import os
    os.system('sudo pip install -U --force-reinstall scipy')
  diffsquares = [math.pow(len("".join(src[0]).replace(" ","")) \
                          - len("".join(trg[0]).replace(" ","")),2) \
                for src, trg in izip(readSentences(srcfile),readSentences(trgfile))]
  src_paragraph_len = [len(i[0]) for i in readSentences(srcfile)]
  (m,_)= polyfit(src_paragraph_len,diffsquares,1)
  return m
'''

def gale_church_alignment(sl_sentences, tl_sentences, mean=1.0, variance=6.8, bc = BEAD_COSTS):
  """ Apply Gale-Church algorithm to align SL with TL sentences.
  
  Arguments:
    sl_sentences (list) -- Source language sentences with paragraph markers (<P>).
    tl_sentences (list) -- Target language sentences with paragraph markers (<P>).
    mean (float) -- Mean of SL/TL character emmission rate; default = 1.0.
    variance (float) -- Variance of SL/TL character emmission; default = 6.8.
    bc (dict) -- Bead costs.

  Returns:
    segments_sl (list) -- SL sentences, equal in length as segments_tl; aligned SL/TL sentences are matched by list index.
    segments_tl (list) -- TL sentences, equal in length as segments_sl; aligned SL/TL sentences are matched by list index.
  """
    
  segments_sl = []
  segments_tl = []
  # If "gacha" instead of float value passed to function, calculate mean and variance
  if mean == "gacha":
    mean = calculateMean(sl_sentences, tl_sentences)
  mean, variance = list(map(float,[mean,variance]))
  
  for src,trg in zip(readSentences(sl_sentences),readSentences(tl_sentences)):
    assert src[1] == trg[1]
    segments_sl.append(src[1])
    segments_tl.append(src[1])
    for (sentence_x, sentence_y) in align(src[0], trg[0], mean, variance, bc):
      segments_sl.append(sentence_x)
      segments_tl.append(sentence_y)
      x = len(segments_sl)
      y = len(segments_tl)
  segments_sl.append("<P>")
  segments_tl.append("<P>")
  return segments_sl, segments_tl