### Natural Language Processing assignment
### Student ID: 1769880

# Part 1: Tagging information


# Get name of untagged emails
from os import listdir
from os.path import isfile, join

myPath = "untagged/"
onlyfiles = [f for f in listdir(myPath) if isfile(join(myPath, f))]


# Reading the corpora
# Declare hash map of files
mapFiles   = {}
mapHeaders = {}
mapContent = {}

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


# Tag times using regex's
import re
stimeRegEx = "\\b((1[0-2]|0?[1-9])((:[0-5][0-9])?)(\s?)([AaPp][Mm])|(1[0-2]|0?[1-9])(:[0-5][0-9])){1}"
testFileName = "303.txt"
print(re.findall(stimeRegEx, mapContent[testFileName]))