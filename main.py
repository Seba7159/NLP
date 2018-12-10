### Natural Language Processing assignment
### Student ID: 1769880

# Imports
import ast
import re
import nltk
import string
import http.client, urllib.request, urllib.parse, urllib.error, json
import gensim
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from nltk.corpus import stopwords
from os import listdir
from os.path import isfile, join
from nltk.corpus import wordnet as wn

# Using stop words to cut any word that is not useful to our tagger
stopws = stopwords.words('english')


# Declarations of hash map for files and tag details
mapFiles    = {}
mapHeaders  = {}
mapContent  = {}
mapTags     = {}
nameData    = []
famData     = ["Mr.", "Mr", "Ms.", "Ms", "Mrs.", "Mrs", "Dr.", "Dr", "Prof.", "Prof"]


# Define speakers and locations to get from training data
training_speakers = ['']
training_locations = ['']


# Define categories and sub-categories
categoryMap = {}
categoryMap['computer science'] = ['artificial intelligence', 'human computer interaction', 'cyber security', 'teaching', 'robotics']
categoryMap['engineering'] = ['mechanical', 'electrical', 'chemical', 'mechatronics']
categoryMap['chemistry'] = ['computational', 'organic', 'physical']
categoryMap['physics'] = ['nuclear', 'atomic', 'electronics', 'particle', "thermodynamics", "relativity", "quantum"]
categoryMap['mathematics'] = ['algebra', 'geometry', 'calculus', 'data science', 'logic']



# Reading the corpora
def readContents():
    # Get name of untagged emails
    myPath = "untagged/"
    onlyfiles = [f for f in listdir(myPath) if isfile(join(myPath, f))]
    onlyfiles = sorted(onlyfiles)

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
            try:
                position = stopws.index(name.lower())
            except ValueError:
                nameData.append(name)

    file = open('names/names.family', "r")
    content = file.read().split("\n")
    for name in content:
        famData.append(name)
    for c in string.ascii_lowercase:
        famData.append(c + ".")


# Method to read the categories for ontology creation
def getCategories():
    # Open the file containing categories
    with open('categories.txt', 'r') as categoriesFile:
        # Return fil content to program's category map
        return ast.literal_eval(categoriesFile.read())


# Method to clean tags from string
def clean_tags(s):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', s)
    return cleantext


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
            if (" "+name.lower()+" ") in mapFiles[fileName].lower() and name is not "":
                nameFound = name
                break
            elif (" "+name.lower()+"<") in mapFiles[fileName].lower() and name is not "":
                nameFound = name
                break
            elif (">"+name.lower()+" ") in mapFiles[fileName].lower() and name is not "":
                nameFound = name
                break
            elif (">"+name.lower()+"<") in mapFiles[fileName].lower() and name is not "":
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


# Method to NER tag text and extract information
def NERtag(fileName):
    # Define entities
    entities = []

    # Tag each paragraph using NER
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
                tagged_words = nltk.pos_tag(nltk.word_tokenize(sent))
                namedEnt = nltk.ne_chunk(tagged_words)

                for ent in namedEnt:
                    if type(ent) is not tuple:
                        entString = repr(ent)[6:][:-11]
                        splitString = entString.split("', [('")
                        typeEnt = splitString[0]
                        nameEnt = ""
                        if len(splitString) > 1:
                            for word in splitString[1].split("', 'NNP'), ('"):
                                nameEnt += word + " "
                            nameEnt = nameEnt[:-1]
                        entities.append((typeEnt, nameEnt))

    entities = list(set(entities))
    # Return the entities tuple array
    return entities



# Method to get url data
def get_url(domain, url):
    # Headers are used if you need authentication
    headers = {}

    # If you know something might fail - ALWAYS place it in a try ... except
    try:
        conn = http.client.HTTPSConnection( domain )
        conn.request("GET", url, "", headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return data
    except Exception as e:
        # These are standard elements in every error.
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

    # Failed to get data!
    return None


# Get data from url
def get_url_data(query):
    # This makes sure that any funny charecters (including spaces) in the query are
    # modified to a format that url's accept.
    query = urllib.parse.quote_plus(query)

    # Call our function.
    url_data = get_url('en.wikipedia.org', '/w/api.php?action=query&list=search&format=json&srsearch=' + query)

    # We know how our function fails - graceful exit if we have failed.
    if url_data is None:
        print("Failed to get data ... Can not proceed.")
        # Graceful exit.
        return ""

    # http.client socket returns bytes - we convert this to utf-8
    url_data = url_data.decode("utf-8")

    # Convert the structured json string into a python variable
    url_data = json.loads(url_data)

    # Define array to be returned
    returnArray = []

    # Find all title searches
    if 'query' in url_data:
        for i in url_data['query']['search']:
            if 'title' in i:
                word = i['title']
                word = ''.join(ch for ch in word if ch not in set(string.punctuation))
                for a in word.split(" "):
                    returnArray.append(a.lower())

    # Return the array with titles
    return returnArray


# Method to calculate the category by relevant words and file name
def calculateCategory(model, relevantWords):
    sumCategories = {}

    # Initialise every tag with 0
    for ontology in categoryMap:
        sumCategories[ontology] = 0

        # Calculate for each word in the relevant words array
        for word in relevantWords:
            try:
                # sumCategories[ontology] += (wn.synset(ontology.split(" ")[0] + ".n.1").path_similiarity(wn.synset(word.replace(" ", "_") + ".n.1")))
                sumCategories[ontology] += model.similarity(ontology.split(" ")[0], word)
            except KeyError as e:
                # print(ontology, word, e)
                relevantWords.remove(word)

    # See maximum for each ontology
    maximumOntology = ""
    maxNumber = -1
    for ontology in categoryMap:
        if sumCategories[ontology] > maxNumber:
            maxNumber = sumCategories[ontology]
            maximumOntology = ontology

    # Now check the sub-categories of the maximum ontology and see if there is any well suited up
    sumCategories = {}
    for subcategory in categoryMap[maximumOntology]:
        sumCategories[subcategory] = 0

        # Calculate for each word in the relevant words array
        for word in relevantWords:
            try:
                sumCategories[subcategory] += model.similarity(subcategory.split(" ")[0], word)
            except KeyError as e:
                print(subcategory, word, e)
                pass

    # See maximum for each ontology again
    maximumOntologySub = ""
    maxNumberSub = -1
    for ontology in categoryMap[maximumOntology]:
        if sumCategories[ontology] > maxNumberSub:
            maxNumberSub = sumCategories[ontology]
            maximumOntologySub = ontology

    # If no match was found
    if maxNumber is 0:
        return ("", "")
    elif maxNumberSub is 0:
        return (maximumOntology, "")

    # Return the maximum number category
    return (maximumOntology, maximumOntologySub)


# Main code
if __name__ == '__main__':
    # Download nltk data
    # nltk.download()

    # Read the file contents from the 'untagged' folder and get training data entities
    readContents()
    obtainTrainingData(training_speakers, training_locations)

    # Part I: Tagging information

    # TODO: delete this after you finished tagging only for one file
    mapTemp = {}
    mapTemp['453.txt'] = ""

    # Go through all files
    print("Tagging started.. ")
    for fileName in mapFiles: #actually mapFiles
        # Initialise key for hash map tags
        mapTags[fileName] = {}
        # Tag in order
        tagTopic(fileName)
        tagParagraphsAndSentences(fileName)
        tagLocation(fileName)
        tagSpeaker(fileName)
        tagTimes(fileName)

    # Tag locations only and the items from the database
    # for fileName in mapFiles:
    #     if 'location' not in mapTags[fileName]:
    #         tagLocation(fileName)

    # Print files
    for fileName in mapFiles:
        # Print content in program
        #print(fileName + "\n" + str(mapFiles[fileName]) + "\n\n")

        # Print content to the tagged/ directory
        file = open("tagged/" + fileName, "w")
        file.write(mapFiles[fileName])

    # Print end message for part 1
    print("Finished tagging files!\n")


    # Part II: Ontology creation

    # Beginning message
    print("Creating ontologies..")
    categoryMap = getCategories()

    # Load Word2Vec model
    print("  Loading Word2Vec... (this might take a while)")
    model = gensim.models.KeyedVectors.load_word2vec_format('../word2vec/GoogleNews-vectors-negative300.bin', binary=True)
    print("  Word2Vec has been successfully loaded!\n")

    # Print all categories to file
    file = open("ontology.txt", "w")

    # Print header for table
    headerPrint = "{f:6s}           {c:16s}            {s}".format(f="FILE NAME", c="CATEGORY", s="SUB-CATEGORY")
    file.write(headerPrint)
    print(headerPrint)

    # For each file, use a NER tagger to extract entities
    for fileName in mapFiles:
        # NER tag each file content
        nerList = NERtag(fileName)

        # Define array of all words to be searched by
        relevantWords = []

        # Add relevant words from NER tags
        for nerElement in nerList:
            # Take data about that NER element from Wikipedia
            relevantWords += get_url_data(nerElement[1])
            pass

        # Clean array to have a relevant word list set up correctly
        relevantWords = list(set(relevantWords))

        # Add the topic words to relevant
        if 'topic' in mapTags[fileName]:
            for word in mapTags[fileName]['topic'].split(" "):
                word = ''.join(ch for ch in word if ch not in set(string.punctuation))
                # Weigh topic words to be 3 times as important as NER tagger words
                for i in range(3):
                    relevantWords.append(word.lower())

        # Now for each word, check the similarity to each category
        mapTags[fileName]['category'], mapTags[fileName]['subcategory'] = calculateCategory(model, relevantWords)

        # Print filename, category and subcategory
        printString = "{f:6s}           {c:16s}            {s}".format(f=fileName, c=mapTags[fileName]['category'], s=mapTags[fileName]['subcategory'])
        file.write(printString)
        print(printString)

    # End message for part 2
    print("Ontology creation has been finished!")


    # End program
    exit(0)