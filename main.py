### Natural Language Processing assignment
### Student ID: 1769880

# Imports
import ast
import nltk
import string
import http.client, urllib.request, urllib.parse, urllib.error, json
import gensim
import warnings

import tagging

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

# Defining first and surnames to get from 'names' data
nameData    = []
famData     = ["Mr.", "Mr", "Ms.", "Ms", "Mrs.", "Mrs", "Dr.", "Dr", "Prof.", "Prof"]

# Define categories and sub-categories map
categoryMap = {}



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


    # Part I: Tagging information

    # Print start message for part 1
    print("Tagging started.. ")

    # Call tagging.py main to do this part
    tagging.main(mapFiles, mapTags, mapHeaders, mapContent, nameData)

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