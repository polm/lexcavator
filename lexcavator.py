#!/usr/bin/env python3
import spacy
import sys, json, random
from nltk.corpus import wordnet as wn
from collections import defaultdict

en = spacy.load('en')

def has_hypernym(word, hyper, pos=wn.NOUN):
    hypers = wn.synsets(hyper)
    pos_filter = lambda x: x.pos() == pos
    senses = list(filter(pos_filter, wn.synsets(word)))
    if not senses: return False

    # the first sense is the most common one, so only use that
    sense = senses[0] 
    for hh in hypers:
        lch = sense.lowest_common_hypernyms(hh)
        if lch and lch[0] == hh:
            return True

    return False

junk = frozenset('one someone such own only'.split())
junktags = frozenset('PRP WP'.split())
def garbage(word):
    ws = str(word)
    if ws in junk: return True
    if word.tag_ in junktags: return True
    if word.lemma_ == '-PRON-': return True
    if word.tag_ == 'JJ' and has_hypernym(str(word), 'numerousness', wn.ADJ): return True
    return False

def is_person(word):
    # words that are a color and a person are typically racist or weird
    return has_hypernym(word, 'person') and not has_hypernym(word, 'color')

def is_location(word):
    # buildings and locations both work, but exclude body parts
    # "mouth", "butt" are locations but only in specific geographic contexts
    return ((has_hypernym(word, 'location') or has_hypernym(word, 'structure')) 
            and not has_hypernym(word, 'body part'))

def is_item(word):
    # for handheld items like pens, swords, tools, etc.
    # pretty fuzzy, needs tuning
    return has_hypernym(word, 'artefact')

def get_words(text):
    out = defaultdict(set)
    doc = en(text)
    for sentence in doc.sents:
        for word in sentence:
            if garbage(word): continue
            if word.tag_ == 'JJ':
                out['jj'].add(word.lemma_)
            if word.pos_ == 'NOUN':
                ws = str(word)
                if is_person(ws):
                    out['person'].add(word.lemma_)
                if is_location(ws):
                    out['location'].add(word.lemma_)
                if is_item(ws):
                    out['item'].add(word.lemma_)

    # convert to lists so we can dump to json
    for key in out.keys():
        out[key] = sorted(list(out[key]))
    return out

if __name__ == '__main__':
    print(json.dumps(get_words(open(sys.argv[1]).read())))
