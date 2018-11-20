### Natural Language Processing assignment
### Student ID: 1769880

# Part 1: Tagging information


# Get name of untagged emails
from os import listdir
from os.path import isfile, join

myPath = "untagged/"
onlyfiles = [f for f in listdir(myPath) if isfile(join(myPath, f))]


# Declare hash map of files
mapFiles   = {}
mapHeaders = {}
mapContent = {}


# Reading the corpora
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


# Testing if a file has been added correctly
print("Header: \n" + mapHeaders["301.txt"])
print("Content: \n" + mapContent["301.txt"])