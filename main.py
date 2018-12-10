##### Natural Language Processing assignment
##### Student ID: 1769880

### Imports
import ast
import string
import gensim
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import evaluator
import ontology_creator
import tagging

from nltk.corpus import stopwords
from os import listdir
from os.path import isfile, join


### Definitions
# Using stop words to cut any word that is not useful to our tagger
stopws = stopwords.words('english')
# Declarations of hash map for files and tag details
mapFiles = {}
mapHeaders = {}
mapContent = {}
mapTags = {}
# Defining first and surnames to get from 'names' data
nameData = []
famData = ["Mr.", "Mr", "Ms.", "Ms", "Mrs.", "Mrs", "Dr.", "Dr", "Prof.", "Prof"]
# Define categories and sub-categories map
categoryMap = {}


### Methods
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


### Main method to run the whole project
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

    # Print evaluator values
    print("Evaluating..")
    evaluator.main()
    print("Evaluator ended.\n") 

    # Part II: Ontology creation
    # Beginning message
    print("Creating ontologies..")
    categoryMap = getCategories()
    # Load Word2Vec model
    print("  Loading Word2Vec... (this might take a while)")
    model = gensim.models.KeyedVectors.load_word2vec_format('../word2vec/GoogleNews-vectors-negative300.bin',
                                                            binary=True)
    print("  Word2Vec has been successfully loaded!\n")
    # Run ontology creation from ontology_creator 'main' method
    ontology_creator.main(model, mapFiles, mapTags, categoryMap, mapContent)
    # End message for part 2
    print("Ontology creation has been finished!")

    # End program
    exit(0)
