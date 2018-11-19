### Natural Language Processing assignment
### Student ID: 1769880

# Part 1: Tagging information


# Get name of untagged emails
from os import listdir
from os.path import isfile, join

myPath = "untagged/"
onlyfiles = [f for f in listdir(myPath) if isfile(join(myPath, f))]
print(onlyfiles)


# Reading the corpora
import nltk
corpus_root = 'untagged/'
corpus = nltk.corpus.reader.plaintext.PlaintextCorpusReader(corpus_root, onlyfiles)
print(corpus)


#