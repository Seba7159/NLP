# NLP algorithm evaluator

# Imports
import re

from os import listdir
from os.path import isfile, join


# Define file names to have
filenames = []


# Method to read the file names
def readFileNames():
    filenames = [f for f in listdir("tagged/") if isfile(join("tagged/", f))]


# Find words by the given tag in the content
def find_by_tag(content, tag):
    # Define tags
    start_tag = "<" + tag + ">"
    end_tag = "</" + tag + ">"

    # Define regular expression to find tag
    pattern = re.compile(start_tag + "(.*?)" + end_tag)

    # Define list to return
    returnList = []

    # Iterate through all found tagged words
    for a in re.findall(pattern, content):
        returnList.append(a)

    # Return the return list
    return returnList

# Method to get all measures like TP, FP and FN
def get_measures(tagged, test):
    # Define true pos, false pos and false pos
    tp = 0
    fp = 0
    fn = 0

    # Find true positives
    for tag in tagged:
        if tag in test:
            tp += 1
            tagged.pop(tagged.index(tag))
            test.pop(test.index(tag))

    # Calculate false positives and negatives
    fp = len(test)
    fn = len(tagged)

    # Return triplet
    return (tp, fp, fn)


# Main code
if __name__ == '__main__':
    # Read the file names
    readFileNames()

    # TEMPORARY
    filenames = ['303.txt']

    # Tags we have
    tags = ["stime", "etime", "location", "speaker", "topic", "paragraph", "sentence"]

    # For each file in the folders
    for file in filenames:
        # Get both paths
        taggedFilePath   = "tagged/" + file
        test_taggedFilePath = "test_tagged/" + file

        # Get contents
        taggedContent   = open(taggedFilePath, "r").read()
        test_taggedContent = open(test_taggedFilePath, "r").read()

        # For each tag, calculate true and false positives or negatives
        total_tp = 0
        total_fp = 0
        total_fn = 0
        for tag in tags:
            # Get the tagged content
            taggedTag   = find_by_tag(taggedContent, tag)
            test_taggedTag = find_by_tag(test_taggedContent, tag)

            # Calculate true positives, false positives and negatives
            tp, fp, fn = get_measures(taggedTag, test_taggedTag)
            total_tp += tp
            total_fp += fp
            total_fn += fn

        # Define accuracy, precision, recall and f1 measure
        accuracy = 0
        precision = 0
        recall = 0
        f1 = 0

        # Calculate accuracy
        if (total_tp + total_fp + total_fn) == 0:
            accuracy = 100
        else:
            accuracy = total_tp / (total_tp + total_fp + total_fn)

        # Calculate precision
        if (total_tp + total_fp) == 0:
            precision = 100
        else:
            precision = total_tp / (total_tp + total_fp)

        # Calculate recall
        if (total_tp + total_fn) == 0:
            recall = 100
        else:
            recall = total_tp / (total_tp + total_fn)

        # Calculate the f1 measure
        if (precision + recall) == 0:
            f1 = 100
        else:
            f1 = 2 * (precision * recall) / (precision + recall)

        print(accuracy, precision, recall, f1)