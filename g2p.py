# /usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import os
import argparse
import unicodedata
import itertools
import string
import pdb
from pynini import *
from pynini.lib import byte
from pynini.lib import pynutil
from pynini.lib import rewrite

SRC_DIR = os.path.dirname(os.path.abspath(__file__)) # /a/b/c/d/e

# Implements Estonian-specific G2P rules
def pronounce_fst(sigma_star):
  t_list = []
  translit = [
    ("ž" , "š"), 
    ("s~" , "š"),
    ("z~" , "š"),
    ("ø" , "ö"),
    ("q" , "k"),
    ("kk" , "K"),
    ("pp" , "P"),
    ("tt" , "T"),
    ("ph" , "f"),
    ("x" , "ks"),
    ("sch" , "š"), 
    ("cz" , "tš"),
    ("ici" , "itsi"),  
    ("zz" , "ts"),  
    ("w" , "v"),
    ("y" , "i"),
    ("z" , "s"),
    ("ć" , "tš"),
    ("č" , "tš"),
    ("ç" , "ts"),
    ("ĉ" , "tš"),
    ("c" , "k"),
    ("jj" , "ij")
    ]
  vowel = union(u"a", u"e", u"i", u"o", u"u", u"õ", u"ä", u"ö", u"ü")
  t_list.append(cdrewrite(cross("ch", u"tš"), "[BOS]", vowel, sigma_star))
  t_list.append(cdrewrite(cross("chr", "kr"), "[BOS]", "", sigma_star))
  t_list.append(cdrewrite(cross("ch", "hh"), vowel, "", sigma_star))
  t_list.append(cdrewrite(cross("ck", "K"), vowel, "", sigma_star))
  t_list.append(cdrewrite(cross("c", "s"), "", "i", sigma_star))
  t_list.append(cdrewrite(cross("c", "ts"), union("r", "l", "n"), union("e", "i"), sigma_star))

  t_list.append(cdrewrite(string_map(translit).closure(), "", "", sigma_star))

  t_list.append(cdrewrite(cross("sh", u"š"), union(vowel, "[BOS]"), vowel, sigma_star, mode="opt"))
  
  plosive_lc = union(*(u"aeiouõäöümnlrv"))
  plosive_rc = union(union(*(u"lrmnvjaeiouõäöü")), "[EOS]")
  
  t_list.append(cdrewrite(cross("k", "K"), plosive_lc, plosive_rc, sigma_star))
  t_list.append(cdrewrite(cross("p", "P"), plosive_lc, plosive_rc, sigma_star))
  t_list.append(cdrewrite(cross("t", "T"), plosive_lc, plosive_rc, sigma_star))
  
  t_list.append(cdrewrite(cross("g", "k"), "", "", sigma_star))
  t_list.append(cdrewrite(cross("b", "p"), "", "", sigma_star))
  t_list.append(cdrewrite(cross("d", "t"), "", "", sigma_star))
  
  t_list.append(cdrewrite(cross("i", "ij"), vowel, difference(vowel, "i"), sigma_star))
  #t_list.append(cdrewrite(cross("i", "j"), difference(sigma_star, vowel), difference(vowel, "i"), sigma_star, mode="opt"))
  
  result = sigma_star
  for t_i in t_list:
    result = result @ t_i
  return result.optimize()


def variants_fst(sigma_star):
  vowels = union("a", "e", "i", "o", "u", "õ", "ä", "ö", "ü")
  r1 = union(sigma_star, cdrewrite(cross("selle", "sele"), "[BOS]", "", sigma_star))
  r2 = union(sigma_star, cdrewrite(cross("nud", "nd"), vowels, "[EOS]", sigma_star))
  r3 = union(sigma_star, cdrewrite(cross(u"äe", u"ää"), sigma_star, "", sigma_star))
  t_file = string_file(SRC_DIR + "/conf/variants.txt")
  r_file = union(sigma_star, cdrewrite(t_file, "[BOS]", "[EOS]", sigma_star))
  return (r1 @ r2 @ r3 @ r_file).optimize()

def rewrite_fst(sigma_star):
  rewrite_map = {}
  for l in open(SRC_DIR + "/conf/rewrites.txt"):
    ss = l.split()
    if len(ss) > 1:
      rewrite_map[ss[0]] = ss[1:]
  result = sigma_star
  for word in sorted(rewrite_map, key=len, reverse=True):
    rewrites = rewrite_map[word]
    combined = None
    for rewrite1 in rewrites:
      r = cdrewrite(cross(word, rewrite1), "[BOS]", "", sigma_star)
      if combined is not None:
        combined = union(combined, r)
      else:
        combined = r
    result = (result @ combined).optimize()
  return result
   
def number_fst(inflection, sigma_star):
  pass

def spell_fst(sigma_star):
  lowercase_letters = union(*(u"abcdefghijklmnoprstuvõäöüxyz"))
  numbers = union(*(u"1234567890")).closure().optimize()
  punctuation = union(*(u"-'/_")).closure().optimize()
  t_file = string_file(SRC_DIR + "/conf/letters.map")
  result = cdrewrite(t_file.closure(2, 4), union(lowercase_letters, numbers, punctuation, "[BOS]"), union(lowercase_letters, numbers, punctuation, "[EOS]"), sigma_star)

  return result.optimize()

def rmdiacritics(char):

    '''
    Return the base character of char, by "removing" any
    diacritics like accents or curls and strokes and the like.
    '''
    desc = unicodedata.name(char)
    cutoff = desc.find(' WITH ')
    if cutoff != -1:
        desc = desc[:cutoff]
    try:
      return unicodedata.lookup(desc)
    except:
      return char

def get_transformer():
  input_chars = list(u"0123456789-+/_.:'~")
  input_chars.extend(list(u"abcdefghijklmnoprsštuvwõõäöüxyzž"))
  input_chars.extend(u"ćçčĉø")
  input_chars.extend([c.upper() for c in input_chars])
  
  #sigma_star = string_map(input_chars, input_token_type="utf8", output_token_type="utf8").project('output').closure().optimize()
  #sigma_star = union(*input_chars).closure().optimize()
  sigma_star = closure(byte.BYTE).optimize()
  
  lowercaser_pairs = {}
  for c in input_chars:
    if c.lower() != c:
      lowercaser_pairs[c] = c.lower()
  lowercaser = string_map(lowercaser_pairs.items())

  uncapitalizer = cdrewrite(lowercaser, "[BOS]", "", sigma_star)

  latin_simplifier_pairs = {}
  for c in input_chars:
    if c.lower() not in set(u'öäõüžš'):
      latin_simplifier_pairs[c] = rmdiacritics(c)
    else:
      latin_simplifier_pairs[c] = c
  latin_simplifier = string_map(latin_simplifier_pairs.items()).closure()

  spell = spell_fst(sigma_star)
  rewriter = rewrite_fst(sigma_star)
  variants = variants_fst(sigma_star)
  pronounce = pronounce_fst(sigma_star)

  transformer = (rewriter @ uncapitalizer @  variants @ pronounce).optimize()
  return transformer


class P2G():
  def __init__(self, fst_file=None):
    transformer = get_transformer()
    self.inverse_transformer = transformer.copy()
    self.inverse_transformer.invert()
    self.inverse_transformer.optimize()
    self.char_lm = None
    if fst_file is not None:
      self.char_lm = Fst.read(fst_file)
      assert self.char_lm.output_symbols(), "No LM output symbol table found"      
      lm_syms = self.char_lm.output_symbols()      
      lexicon = [w for (l, w) in lm_syms if l > 0]
      lexicon_fsa = string_map(lexicon).optimize()
      self.lm_mapper = string_map(
        lexicon, input_token_type="byte", output_token_type=lm_syms)
      self.bytes_to_lm_mapper = self.lm_mapper.closure()
      self.lm_to_bytes_mapper = invert(self.bytes_to_lm_mapper)      

  def process(self, pron, num_nbest=1):
    pron = pron.replace("sh", "š").replace("ou", u"õ").replace("ae", "ä").replace("oe", "ö").replace("ue", "ü").replace("kk", "K").replace("pp", "P").replace("tt", "T").replace(" ", "")
    orig_pron = accep(pron)
    lattice = (orig_pron @ self.inverse_transformer).project('output')
    lattice.optimize()
    if self.char_lm:
      lattice = rewrite.rewrite_lattice(lattice, self.bytes_to_lm_mapper)
      lattice = rewrite.rewrite_lattice(lattice, self.char_lm)
      lattice = rewrite.rewrite_lattice(lattice, self.lm_to_bytes_mapper)        
      
    lattice.optimize()
    
    shortest_paths = shortestpath(lattice, nshortest=num_nbest, unique=False)
    result = []
    for word, weight in zip(shortest_paths.paths().ostrings(), shortest_paths.paths().weights()):
      result.append((word, weight))
    return result
    

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Apply G2P rules for Estonian')
  parser.add_argument('--inverse', default=False, action='store_true', help='Use inverse rules')
  parser.add_argument('--fst', default="", help="FST for ranking results")
  parser.add_argument('--nbest', type=int, default=3, help="Max number of hypotheses")
  args = parser.parse_args()

  

  if args.inverse:
    p2g = P2G(args.fst)
      
    while 1:
      l = sys.stdin.readline()   
      if not l : break 
      orig_pron = l.strip().replace(" ", "_")
      for i, (word, weight) in enumerate(p2g.process(l.strip(), num_nbest=args.nbest)):
        variant_id_str = ""
        if i > 0:
          variant_id_str = "(%d)" % (i+1)
        print(orig_pron, word, weight)
        sys.stdout.flush()
  else:    
    g2p = get_transformer()
    while 1:
      l = sys.stdin.readline()    
      if not l : break
      word = l.strip()
      orig_word = accep(word)
      lattice = optimize((orig_word @ g2p).project('output'))
      
      for (i, pronunciation) in enumerate(shortestpath(lattice.project('input'), nshortest=args.nbest, unique=True).paths().ostrings()):        
        pronunciation = u" ".join(list(pronunciation))
        pronunciation = pronunciation.replace(u"š", "sh").replace(u"õ", "ou").replace(u"ä", "ae").replace(u"ö", "oe").replace(u"ä", "ue").replace(u"K", "kk").replace(u"P", "pp").replace(u"T", "tt")
        variant_id_str = ""
        if i > 0:
          variant_id_str = "(%d)" % (i+1)          
        print(orig_word.string(), pronunciation)
        sys.stdout.flush()
    
  
