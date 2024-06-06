## FST-based rule-based grapheme-to-phoneme (and vice versa) converter for Estonian

Requires:
  * Pynini (http://pynini.opengrm.org)
  
# Usage:
    
Input: text file, containing words, one per line:

    $ cat test.txt 
    tere
    katki
    katik
    kattes
    šokolaad

    $ cat test.txt | python g2p.py 
    tere t e r e
    katki k a t k i
    katik k a tt i kk
    kattes k a tt e s
    šokolaad sh o kk o l a a t
