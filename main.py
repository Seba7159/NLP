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
nameData    = []
famData     = []

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
    
    # Put names in database
    onlyfilesname = ['names/names.male', 'names/names.female']
    for fileName in onlyfilesname:
        file = open(fileName, "r")
        content = file.read().split("\n")
        for name in content:
            nameData.append(name)

    file = open('names/names.family', "r")
    content = file.read().split("\n")
    for name in content:
        famData.append(name)


# Method for tagging words
def tag(position, word, fileName, tagName):
    # Create tag strings
    startTag = "<" + tagName + ">"
    finalTag = "</" + tagName + ">"

    # Tag sentence before the dot
    if tagName is 'sentence' and len(word) > 0 and word[len(word)-1] is '.':
        word = word[:-1]

    # Tag paragraph before a '\n' character
    if tagName is 'paragraph' and len(word) > 0 and word[len(word)-1] is '\n':
        word = word[:-1]

    # Tag paragraph after \n
    if tagName is 'paragraph' and len(word) > 0 and word[0] is '\n':
        word = word[1:]

    # Add tag at end of word
    content = mapFiles[fileName]
    content = content[:(position + len(word))] + finalTag + content[(position + len(word)):]
    content = content[:position] + startTag + content[position:]
    mapFiles[fileName] = content


# Method to find all occurences
def find_all(a_str, sub):
    if len(sub) is 0:
        return
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)


# Normalise time
def normalise_time(time):
    ampm = ['a', 'A', 'p', 'P']
    # ampmPart = ""
    restTime = time.strip()
    for c in ampm:
        if c in time:
            # ampmPart = time[time.find(c):].replace(string.punctuation, "").lower()
            restTime = time[:time.find(c)].strip()
    if ":" in restTime:
        getHM = restTime.split(":")
        return (getHM[0], getHM[1])
    elif "." in restTime:
        getHM = restTime.split(".")
        return (getHM[0], getHM[1])
    else:
        return (restTime, "00")


# Tag times using regex's
def tagTimes(fileName):
    if "stime" not in mapTags[fileName]:
        # Tag start and end time from headers
        headerRegEx = "Time:(.*)"
        headerTimesTemp = re.search(headerRegEx, mapHeaders[fileName])

        # If header times are not found
        if headerTimesTemp is None:
            return

        # Split header times by the '-' character
        headerTimes = headerTimesTemp.group(1).split("-")

        # For each possible case if it was split or not
        if len(headerTimes) == 1:
            mapTags[fileName]['stime'] = headerTimes[0].strip()
        elif len(headerTimes) >= 2:
            mapTags[fileName]['stime'] = headerTimes[0].strip()
            mapTags[fileName]['etime'] = headerTimes[1].strip()

    # Find times in content
    stimeRegEx = re.compile("\\b((1[0-2]|0?[1-9])(((:|\.)[0-5][0-9])?)(\s?)([AaPp](\.?)[Mm])|(1[0-2]|0?[1-9])((:|\.)[0-5][0-9])){1}")
    etimeRegEx = re.compile("\\b((1[0-2]|0?[1-9])(((:|\.)[0-5][0-9])?)(\s?)([AaPp](\.?)[Mm](\.?))|(1[0-2]|0?[1-9])((:|\.)[0-5][0-9])){1}")

    # Check how many positions have advanced
    counter = 0
    TIME_TAG_LEN = len("<stime></stime>")

    # Add tags at start time
    if "stime" in mapTags[fileName]:
        for m in stimeRegEx.finditer(mapFiles[fileName]):
            position = m.start() + counter * TIME_TAG_LEN
            wordToTag = m.group().strip()
            if normalise_time(wordToTag.lower())   == normalise_time(mapTags[fileName]['stime'].lower()):
                tag(position, wordToTag, fileName, 'stime')
                counter += 1

    # Add tags for end time
    counter = 0
    if "etime" in mapTags[fileName]:
        for m in etimeRegEx.finditer(mapFiles[fileName]):
            position = m.start() + counter * TIME_TAG_LEN
            wordToTag = m.group().strip()
            if normalise_time(wordToTag.lower())   == normalise_time(mapTags[fileName]['etime'].lower()):
                tag(position, wordToTag, fileName, 'etime')
                counter += 1

    # End method for time tagging
    return


# Method for tagging paragraphs
def tagParagraphsAndSentences(fileName):
    # Find paragraphs
    for paragraph in mapContent[fileName].split("\n\n"):
        words = nltk.word_tokenize(paragraph.lower())
        isParagraph = False

        # If there is no verb or there are words like "WHEN:", it's not a paragraph
        for word, part in nltk.pos_tag(words):
            if part[0] == 'V':
                isParagraph = True
                break
            if word is ":":
                break

        # Tag paragraph if it is true
        if isParagraph == True:
            position = mapFiles[fileName].find(paragraph)
            tag(position, paragraph, fileName, "paragraph")

            # Now tag sentences from each paragraph
            sentences = nltk.sent_tokenize(paragraph)
            for sent in sentences:
                sent = sent.strip()
                position = mapFiles[fileName].lower().find(sent.lower())
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
            if punct is not '.':
                headerSpeaker = headerSpeaker.split(punct)[0]
        if headerSpeaker is '':
            continue
        else:
            mapTags[fileName]['speaker'] = headerSpeaker
            break

    # If not found, try to find names in the content
    if 'speaker' not in mapTags[fileName]:
        namesFound = []
        for name in nameData:
            if (" "+name+" ") in mapFiles[fileName] and name is not "":
                namesFound.append(name)
        # To check if names appear in text and call it the speaker

    # If still not found, get a greedy approach such as the first name that appears in the content of file
    if 'speaker' not in mapTags[fileName]:
        for paragraph in mapContent[fileName].split("\n\n"):
            # Stop using NER because it is not working correctly
            break

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
                    tagged_words = nltk.pos_tag(nltk.word_tokenize(sent))
                    namedEnt = nltk.ne_chunk(tagged_words)

                    # For each sentence, if a speaker is found, put it as the actual speaker and end the search
                    for name in namedEnt:
                        if "PERSON" in repr(name):
                            mapTags[fileName]['speaker'] = ""
                            for n in name:
                                mapTags[fileName]['speaker'] += n[0] + " "
                            break
                        if 'speaker' in mapTags:
                            break
                if 'speaker' in mapTags:
                    break
            if 'speaker' in mapTags:
                break

    # Tag speaker now if found
    if 'speaker' in mapTags[fileName]:
        # Strip speaker
        mapTags[fileName]['speaker'] = mapTags[fileName]['speaker'].strip()
        counter = 0
        for location in find_all(mapFiles[fileName].lower(), mapTags[fileName]['speaker'].lower()):
            tag(location + counter, mapTags[fileName]['speaker'].lower(), fileName, 'speaker')
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
            #tag(posTemp, headerTopic, fileName, 'topic')
            counter += 1

    # End method
    return


# Method for tagging the location
def tagLocation(fileName):
    # Tag place from headers
    headerRegEx = "Place:(.*)"
    headerLocationTemp = re.search(headerRegEx, mapHeaders[fileName])

    # If header location is found in header
    if headerLocationTemp is not None:
        # If place is found in header, check for words containing it
        headerLocation = headerLocationTemp.group(1).strip()
        mapTags[fileName]['location'] = headerLocation.strip()

    # If location was not found in the header, check for locations from previous text files
    if headerLocationTemp is None:
        for key in mapTags:
            if 'location' in mapTags[key]:
                if mapFiles[fileName].find(mapTags[key]['location']) != -1:
                    mapTags[fileName]['location'] = mapTags[key]['location']
                    break

    # If header location is found
    if headerLocationTemp is not None:
        # Define temporary variables for advanced positions so far
        counter = 0
        LOCATION_TAG_LEN = len("<location></location>")
        topicRegEx = re.compile(re.escape(headerLocation.lower()))

        # Add tags for the found location
        for m in topicRegEx.finditer(mapFiles[fileName].lower()):
            posTemp = m.start() + counter * LOCATION_TAG_LEN
            tag(posTemp, mapTags[fileName]['location'], fileName, 'location')
            counter += 1

    # End method
    return


# Main code
if __name__ == '__main__':
    # Download nltk data
    #nltk.download()

    # Read the file contents from the 'untagged' folder
    readContents()

    # TODO: delete this after you finished tagging only for one file
    mapTemp = {}
    mapTemp['356.txt'] = ""

    # Go through all files
    for fileName in mapFiles: #actually mapFiles
        # Initialise key for hash map tags
        mapTags[fileName] = {}
        # Tag in order
        tagParagraphsAndSentences(fileName)
        tagTopic(fileName)
        tagLocation(fileName)
        tagSpeaker(fileName)
        tagTimes(fileName)

    # Tag locations only and the items from the database
    for fileName in mapFiles:
        if 'location' not in mapTags[fileName]:
            tagLocation(fileName)

    # Print files
    for fileName in mapFiles:
        # Print content in program
        #print(fileName + "\n" + str(mapFiles[fileName]) + "\n\n")

        # Print content to the tagged/ directory
        file = open("tagged/" + fileName, "w")
        file.write(mapFiles[fileName])

    # End program
    exit(0)