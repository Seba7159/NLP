### Imports
import re
import nltk
import string
from os import listdir
from os.path import isfile, join


### Definitions
# Define speakers and locations to get from training data
training_speakers = ['']
training_locations = ['']
name_titles = ["Mr.", "Mr", "Ms.", "Ms", "Mrs.", "Mrs", "Dr.", "Dr", "Prof.", "Prof", "Doctor", "Professor", "Assistant"]


### Methods
# Method to clean tags from string
def clean_tags(s):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', s)
    return cleantext


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


# Method to obtain speakers and locations from training data
def obtainTrainingData(training_speakers, training_locations):
    # Get name of untagged emails
    myPath = "training/"
    training_files = [f for f in listdir(myPath) if isfile(join(myPath, f))]
    training_files = sorted(training_files)

    # Read each file
    for fileName in training_files :
        # Construct file name and read the file
        filePath = myPath + fileName
        file = open(filePath, "r")
        fileContent = file.read()

        # Get speaker and location from there
        get_speaker_regex = re.compile('<speaker>(.*?)</speaker>|$')
        speaker = re.findall(get_speaker_regex, fileContent)[0].split(",")[0]
        training_speakers.append(clean_tags(speaker))

        # Get location and location from there
        get_location_regex = re.compile('<location>(.*?)</location>|$')
        location = re.findall(get_location_regex, fileContent)[0].split(",")[0]
        training_locations.append(clean_tags(location))

    # Remove empty strings
    if ' ' in training_speakers:
        training_speakers.remove(' ')
    if ' ' in training_locations:
        training_locations.remove(' ')
    if '' in training_speakers:
        training_speakers.remove('')
    if '' in training_locations:
        training_locations.remove('')

    # Setify lists
    training_speakers = list(set(training_speakers))
    training_locations = list(set(training_locations))

    # End method
    return


# Method for tagging words
def tag(position, word, fileName, tagName):
    # Create tag strings
    startTag = "<" + tagName + ">"
    finalTag = "</" + tagName + ">"

    # Tag sentence before the dot
    if tagName is 'sentence' and len(word) > 0 and word[len(word)-1] in string.punctuation:
        word = word[:-1]

    # Tag paragraph before a '\n' character
    if tagName is 'paragraph' and len(word) > 0 and word[len(word)-1] is '\n':
        word = word[:-1]

    # Add tag at end of word
    content = mapFiles[fileName]
    content = content[:(position + len(word))] + finalTag + content[(position + len(word)):]
    content = content[:position] + startTag + content[position:]
    mapFiles[fileName] = content


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

        # Check if first letter is alpha or not
        if len(words) > 0 and words[0][0].isalpha() is False:
            isParagraph = False

        # Tag paragraph if it is true
        if isParagraph == True:
            position = mapFiles[fileName].find(paragraph)
            tag(position, paragraph, fileName, "paragraph")

        # Now tag sentences from each paragraph
        sentences = nltk.sent_tokenize(paragraph)
        for sent in sentences:
            if len(sent) > 0 and sent[0].isalpha() is False:
                pass
            else:
                sent = sent.strip()
                position = mapFiles[fileName].lower().find(sent.lower())
                tag(position, sent, fileName, "sentence")

    # End method for paragraph tagging
    return


# Method for tagging the speaker of the annoucement
def tagSpeaker(fileName, nameData, famData):
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

    # If speaker was not found in the header, check for speakers from training files
    if 'speaker' not in mapTags[fileName]:
        for speaker in training_speakers:
            if 'speaker' not in mapTags[fileName]:
                if mapFiles[fileName].find(speaker) != -1 and len(speaker) > 0 and mapFiles[fileName][mapFiles[fileName].find(speaker)-1] is " ":
                    mapTags[fileName]['speaker'] = speaker
                    break

    # If still not found, try to find names in the content by its own starting with a capital letter
    if 'speaker' not in mapTags[fileName]:
        nameFound = ""
        for name in nameData:
            # Check if name exists in text
            if 'topic' not in mapTags[fileName]:
                continue
            if (" "+name.lower()+" ") in mapTags[fileName]['topic'].lower() and name is not "":
                nameFound = name
                break
            elif (" "+name.lower()+"<") in mapTags[fileName]['topic'].lower() and name is not "":
                nameFound = name
                break
            elif (">"+name.lower()+" ") in mapTags[fileName]['topic'].lower() and name is not "":
                nameFound = name
                break
            elif (">"+name.lower()+"<") in mapTags[fileName]['topic'].lower() and name is not "":
                nameFound = name
                break
        # To check if names appear in text and call it the speaker
        if nameFound is not "":
            words = mapFiles[fileName].replace(">", " ").replace(">", " ").replace("\n", " ").split(" ")
            try:
                pos = words.index(nameFound)
            except ValueError:
                pos = -2
            i = pos - 1
            while i >= 0 and len(words[i]) > 0 and words[i][0].isupper():
                nameFound = words[i] + " " + nameFound
                i -= 1
            i = pos + 1
            while i < len(words) and i >= 0 and len(words[i]) > 0 and words[i][0].isupper(): #famFound.find(words[i]) != -1:
                nameFound = nameFound + " " + words[i]
                i += 1
            mapTags[fileName]['speaker'] = re.sub(r'[^\w\s]', '', nameFound)


    # If still not found, use a NER tagger
    if 'speaker' not in mapTags[fileName]:
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
        # Get surname of speaker
        names = mapTags[fileName]['speaker'].split(" ")
        surname = names[len(names)-1].strip()

        # Strip speaker
        mapTags[fileName]['speaker'] = mapTags[fileName]['speaker'].strip()
        counter = 0
        for location in find_all(mapFiles[fileName].lower(), mapTags[fileName]['speaker'].lower()):
            tag(location + counter, mapTags[fileName]['speaker'].lower(), fileName, 'speaker')
            counter += 1 + 2 * len('<speaker>')
        if len(surname) > 0:
            for title in name_titles:
                for location in find_all(mapFiles[fileName].lower(), (title+" "+surname).lower()):
                    tag(location + counter, (title+" "+surname).lower(), fileName, 'speaker')
                    counter += 1 + 2 * len('<speaker>')
                for location in find_all(mapFiles[fileName].lower(), (title+" "+mapTags[fileName]['speaker']).lower()):
                    tag(location + counter, (title+" "+mapTags[fileName]['speaker']).lower(), fileName, 'speaker')
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
        if headerLocation is '' or headerLocation is " ":
            pass
        else:
            mapTags[fileName]['location'] = headerLocation

    # If location was not found in the header, check for locations from previous text files
    if 'location' not in mapTags[fileName]:
        for location in training_locations:
            if mapFiles[fileName].find(location) != -1 and len(location) > 0 and mapFiles[fileName][mapFiles[fileName].find(location)-1] is " ":
                mapTags[fileName]['location'] = location
                break

    # If header location is found
    if 'location' in mapTags[fileName]:
        # Define temporary variables for advanced positions so far
        counter = 0
        LOCATION_TAG_LEN = len("<location></location>")
        topicRegEx = re.compile(re.escape(mapTags[fileName]['location'].lower()))

        # Add tags for the found location
        for m in topicRegEx.finditer(mapFiles[fileName].lower()):
            posTemp = m.start() + counter * LOCATION_TAG_LEN
            tag(posTemp, mapTags[fileName]['location'], fileName, 'location')
            counter += 1

    # End method
    return


## Main method
def main(mapFl, mapTg, mapHd, mapCt, nameData, famData):
    # Put function data in global data
    global mapFiles
    mapFiles = mapFl
    global mapTags
    mapTags = mapTg
    global mapHeaders
    mapHeaders = mapHd
    global mapContent
    mapContent = mapCt

    # Get data from the training files
    obtainTrainingData(training_speakers, training_locations)

    # Go through all files
    for fileName in mapFiles:  # actually mapFiles
        # Initialise key for hash map tags
        mapTags[fileName] = {}
        # Tag in order
        tagTopic(fileName)
        tagParagraphsAndSentences(fileName)
        tagLocation(fileName)
        tagSpeaker(fileName, nameData, famData)
        tagTimes(fileName)

    # Print files
    for fileName in mapFiles:
        # Print content in program
        # print(fileName + "\n" + str(mapFiles[fileName]) + "\n\n")

        # Print content to the tagged/ directory
        file = open("tagged/" + fileName, "w")
        file.write(mapFiles[fileName])

    # End method with True if it worked
    return True