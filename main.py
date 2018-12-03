### Natural Language Processing assignment
### Student ID: 1769880

# Part 1: Tagging information

# Imports
import re
import nltk
import string

from nltk.corpus import treebank
from nltk import tokenize

from os import listdir
from os.path import isfile, join

# Declarations of hash map for files and tag details
mapFiles    = {}
mapHeaders  = {}
mapContent  = {}
mapTags     = {}


# Reading the corpora
def readContents():
    # Get name of untagged emails
    myPath = "untagged/"
    onlyfiles = [f for f in listdir(myPath) if isfile(join(myPath, f))]

    # Read each file
    for fileName in onlyfiles:
        # Construct file name and read the file
        filePath = myPath + fileName
        file = open(filePath, "r")
        fileContent = file.read()

        # Map file content by file name
        mapFiles[fileName] = fileContent

        # Map headers and contents to specific hash maps
        splitter = "Abstract:"
        splitFileContent = fileContent.split(splitter)
        mapHeaders[fileName] = splitFileContent[0]
        if splitter in fileContent:
            mapContent[fileName] = splitFileContent[1]
        else:
            mapContent[fileName] = ""


# Method for tagging words
def tag(position, word, fileName, tagName):
    # Create tag strings
    finalTag = "<\\" + tagName + ">"
    startTag = "<" + tagName + ">"

    # Add tag at end of word
    content = mapFiles[fileName]
    content = content[:(position + len(word))] + finalTag + content[(position + len(word)):]
    content = content[:position] + startTag + content[position:]
    mapFiles[fileName] = content


# Tag times using regex's
def tagTimes(fileName):
    # Tag start and end time from headers
    headerRegEx = "Time:(.*)"
    headerTimesTemp = re.search(headerRegEx, mapHeaders[fileName])

    # If header times are not found
    if headerTimesTemp is None:
        return

    headerTimes = headerTimesTemp.group(1).split("-")

    if len(headerTimes) == 1:
        mapTags[fileName]['stime'] = headerTimes[0].strip()
        mapTags[fileName]['etime'] = "PARAMETER_EMPTY"
    elif len(headerTimes) == 2:
        mapTags[fileName]['stime'] = headerTimes[0].strip()
        mapTags[fileName]['etime'] = headerTimes[1].strip()
    else:
        mapTags[fileName]['stime'] = "PARAMETER_EMPTY"
        mapTags[fileName]['etime'] = "PARAMETER_EMPTY"

    # Find times in content
    timeRegEx = re.compile("\\b((1[0-2]|0?[1-9])((:[0-5][0-9])?)(\s?)([AaPp][Mm])|(1[0-2]|0?[1-9])(:[0-5][0-9])){1}")

    # Check how many positions have advanced
    counter = 0
    TIME_TAG_LEN = len("<stime></stime>")

    # Add tags at start and end of time
    for m in timeRegEx.finditer(mapFiles[fileName]):
        position = m.start() + counter * TIME_TAG_LEN
        wordToTag = m.group().strip()
        if wordToTag.lower()   == mapTags[fileName]['stime'].lower():
            tag(position, wordToTag, fileName, 'stime')
            counter += 1
        elif wordToTag.lower() == mapTags[fileName]['etime'].lower():
            tag(position, wordToTag, fileName, 'etime')
            counter += 1

    # End method for time tagging
    return


# Method for tagging sentences
def tagSentences(fileName):
    # Train the data
    print("Training data..")
    train_sents = treebank.tagged_sents()[:3000]
    print("Data has been trained successfully. ")

    # Create a local backoff tagger method
    def backoff_tagger(train_sents, tagger_classes, backoff=None):
        for cls in tagger_classes:
            backoff = cls(train_sents, backoff=backoff)
        return backoff

    # Call the method so you can get the backoff tagger
    tagger = backoff_tagger(train_sents, [nltk.UnigramTagger, nltk.BigramTagger, nltk.TrigramTagger], backoff=nltk.DefaultTagger('NN'))

    # Test tagger
    print("Evaluating tagger..")
    test_sents = treebank.tagged_sents()[3000:]
    print(tagger.evaluate(test_sents))

    # Define escape characters
    escapes = ''.join([chr(char) for char in range(1, 32)])

    fileContentLine = "";
    for line in mapContent[fileName].split("\n"):
        fileContentLine += line + " ";
    # print(fileContentLine)

    sents = tokenize.sent_tokenize(fileContentLine.replace(escapes, " "))
    # print(sents)

    # End method for paragraph tagging
    return


# Method for tagging paragraphs
def tagParagraphs(fileName):
    # Find paragraphs
    for paragraph in mapContent[fileName].split("\n\n"):
        words = nltk.word_tokenize(paragraph)
        isParagraph = False
        # If there is no verb in the first 5 words, it's not a paragraph
        count = 5
        for word, part in nltk.pos_tag(words):
            count -= 1
            if count <= 0:
                break
            if part[0] == 'V':
                isParagraph = True
                break

        # Define local find string method
        def find_str(s, char):
            index = 0
            if char in s:
                c = char[0]
                for ch in s:
                    if ch == c:
                        if s[index:index + len(char)] == char:
                            return index

                    index += 1
            return -1

        # Tag paragraph if it is true
        if isParagraph == True:
            position = 0 # TODO find position of paragraph and tag it well 
            print(position)
            tag(position, paragraph, fileName, "paragraph")

    print(mapFiles[fileName])

    # End method for paragraph tagging
    return


# Method for tagging the speaker of the annoucement
def tagSpeaker(fileName):
    # Define 'found' boolean
    found = False

    # Tag speaker by given attributes from the whole file
    headerSpeakerRegExs = ["who:(.*)", "speaker:(.*)", "name:(.*)"]
    for regEx in headerSpeakerRegExs:
        headerSpeakerTemp = re.search(regEx, mapFiles[fileName].lower())
        if headerSpeakerTemp is None:
            continue

        # If found, cut punctuation and whitespaces
        headerSpeaker = headerSpeakerTemp.group(1)
        for punct in string.punctuation:
            headerSpeaker = headerSpeaker.split(punct)[0]
        headerSpeaker = headerSpeaker.strip()

    # If still not found, try to find by words such as 'by' or 'with' then see if they are people

    # If still not found, get a greedy approach such as the first name that appears in the content of file

    # Worst case, speaker can't be found



# Method to tag the topic
def tagTopic(fileName):
    # Tag place from headers
    headerRegEx = "Topic:(.*)"
    headerTopicTemp = re.search(headerRegEx, mapHeaders[fileName])

    # If header location is not found   TODO: find more occurences about the topic in the text + find full topic if on multiple lines
    if headerTopicTemp is None:
        return

    # If place is defined in header, check for words containing it
    else:
        # Get topic from header
        headerTopic = headerTopicTemp.group(1).strip()
        mapTags[fileName]['topic'] = headerTopic

        # Define temporary variables for advanced positions so far
        counter = 0
        TOPIC_TAG_LEN = len("<topic></topic>")
        topicRegEx = re.compile(re.escape(headerTopic.lower()))

        # Add tags for the found topic in the header
        for m in topicRegEx.finditer(mapFiles[fileName].lower()):
            posTemp = m.start() + counter * TOPIC_TAG_LEN
            tag(posTemp, headerTopic, fileName, 'topic')
            counter += 1

    # End method
    return


# Method for tagging the location
def tagLocation(fileName):
    # Tag place from headers
    headerRegEx = "Place:(.*)"
    headerLocationTemp = re.search(headerRegEx, mapHeaders[fileName])

    # If header location is not found   TODO: find other locations in the text
    if headerLocationTemp is None:
        return
    # If place is found in header, check for words containing it
    headerLocation = headerLocationTemp.group(1).strip()
    mapTags[fileName]['location'] = headerLocation

    # Define temporary variables for advanced positions so far
    counter = 0
    LOCATION_TAG_LEN = len("<location></location>")
    topicRegEx = re.compile(re.escape(headerLocation.lower()))

    # Add tags for the found topic
    for m in topicRegEx.finditer(mapFiles[fileName].lower()):
        posTemp = m.start() + counter * LOCATION_TAG_LEN
        tag(posTemp, headerLocation, fileName, 'location')
        counter += 1

    # End method
    return


# Main code
if __name__ == '__main__':
    # Download nltk data
    # nltk.download()

    # Read the file contents from the 'untagged' folder
    readContents()

    # Set the file name
    fileName = "303.txt"

    # Initialise key for hash map tags
    mapTags[fileName] = {}

    # Tag in order
    tagParagraphs(fileName)
    tagSentences(fileName)
    tagSpeaker(fileName)
    tagTopic(fileName)
    tagLocation(fileName)
    tagTimes(fileName)

    # Print content
    #print(mapFiles[fileName])