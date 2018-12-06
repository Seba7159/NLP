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
    finalTag = "</" + tagName + ">"
    startTag = "<" + tagName + ">"

    # Add tag at end of word
    content = mapFiles[fileName]
    content = content[:(position + len(word))] + finalTag + content[(position + len(word)):]
    content = content[:position] + startTag + content[position:]
    mapFiles[fileName] = content


# Method to find all occurences
def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)


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


# Method for tagging paragraphs
def tagParagraphsAndSentences(fileName):
    # Find paragraphs
    for paragraph in mapContent[fileName].split("\n\n"):
        words = nltk.word_tokenize(paragraph)
        isParagraph = False

        # If there is no verb or there are words like "WHEN:", it's not a paragraph
        lastWord = "abc"
        for word, part in nltk.pos_tag(words):
            if part[0] == 'V':
                isParagraph = True
                break
            if lastWord.isupper() and word is ":":
                break
            lastWord = word

        # Tag paragraph if it is true
        if isParagraph == True:
            position = mapFiles[fileName].find(paragraph)
            tag(position, paragraph, fileName, "paragraph")

        # Now tag sentences from each paragraph
        if isParagraph == True:
            sentences = nltk.sent_tokenize(paragraph)
            for sent in sentences:
                position = mapFiles[fileName].find(sent)
                tag(position, sent, fileName, "sentence")

    # End method for paragraph tagging
    return


# Method for tagging the speaker of the annoucement
def tagSpeaker(fileName):
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
        mapTags['speaker'] = headerSpeaker.strip()

    # If still not found, get a greedy approach such as the first name that appears in the content of file
    if 'speaker' not in mapTags:
        for paragraph in mapContent[fileName].split("\n\n"):
            words = nltk.word_tokenize(paragraph)
            isParagraph = False
            for word, part in nltk.pos_tag(words):
                if part[0] == 'V':
                    isParagraph = True
                    break
            if isParagraph == True:
                sentences = nltk.sent_tokenize(paragraph)
                for sent in sentences:
                    position = mapFiles[fileName].find(sent)
                    tag(position, sent, fileName, "sentence")
                    tagged_words = nltk.pos_tag(nltk.word_tokenize(sent))
                    namedEnt = nltk.ne_chunk(tagged_words)
                    # For each sentence, if a speaker is found, put it as the actual speaker and end the search
                    for name in namedEnt:
                        if "PERSON" in repr(name):
                            mapTags['speaker'] = ""
                            for n in name:
                                mapTags['speaker'] += n[0] + " "
                            break
                        if 'speaker' in mapTags:
                            break
                if 'speaker' in mapTags:
                    break
            if 'speaker' in mapTags:
                break

    # Tag speaker now if found
    if 'speaker' in mapTags:
        # Strip speaker
        mapTags['speaker'] = mapTags['speaker'].strip()
        counter = 0
        for location in find_all(mapFiles[fileName].lower(), mapTags['speaker'].lower()):
            tag(location + counter, mapTags['speaker'].lower(), fileName, 'speaker')
            counter += 1 + 2 * len('<speaker>')

    # Worst case, speaker can't be found
    return



# Method to tag the topic
def tagTopic(fileName):
    # Tag place from headers
    headerRegEx = "Topic:(.*)"
    headerTopicTemp = re.search(headerRegEx, mapHeaders[fileName])

    # If header location is not found
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
    if headerLocationTemp is not None:
        # If place is found in header, check for words containing it
        headerLocation = headerLocationTemp.group(1).strip()
        mapTags[fileName]['location'] = headerLocation

        # Define temporary variables for advanced positions so far
        counter = 0
        LOCATION_TAG_LEN = len("<location></location>")
        topicRegEx = re.compile(re.escape(headerLocation.lower()))

        # Add tags for the found location
        for m in topicRegEx.finditer(mapFiles[fileName].lower()):
            posTemp = m.start() + counter * LOCATION_TAG_LEN
            tag(posTemp, headerLocation, fileName, 'location')
            counter += 1

    # If location was not found in the header, TODO: find other last locations in text

    # End method
    return


# Main code
if __name__ == '__main__':
    # Download nltk data
    #nltk.download()

    # Read the file contents from the 'untagged' folder
    readContents()

    # Set the file name
    fileName = "303.txt"

    # Initialise key for hash map tags
    mapTags[fileName] = {}

    # Tag in order
    tagParagraphsAndSentences(fileName)
    tagTopic(fileName)
    tagLocation(fileName)
    tagSpeaker(fileName)
    tagTimes(fileName)

    # Print content
    print(mapFiles[fileName])