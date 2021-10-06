import os
import math
import requests
import time
import PyPDF2
from PyPDF2 import PdfFileReader, PdfFileWriter, utils
from pathlib import Path
import pikepdf
from pdfminer.pdfpage import PDFPage
from reportlab.pdfgen.canvas import Canvas
from collections import Counter
from PyDFScraper import Error
from enum import Enum
from distutils.dir_util import copy_tree


def createRapport(year):
    global categories
    global totalOrganisations
    #: Initialise all variables
    initialiseVariables(year)

    #: Categorise all organisations into one of 5 different search categories
    categorise()
    '''
    #: print all info from category
    for category in categories:
    print("Categorie " + category.name)
    print(category.amount)
    print(category.matrix)
    '''

    for category in categories:
        print(category.name + ": " + calculatePercentage(category.amount, totalOrganisations))

    # print()
    print(totalOrganisations)
    print(categories[Categories.encryption.value].amount)

    print(categories[Categories.encryption.value].amount)
    movePdfs(year)
    return "------[THE END]------"


class Category:
    def __init__(self, name):
        self.name = name
        self.amount = 0
        self.matrix = []
        self.organisations = []


class Categories(Enum):
    succes = 0
    fewresults = 1
    encryption = 2
    EOF = 3
    noresults = 4
    nodocument = 5


class SearchTerm(Enum):
    succes = "Wel resultaten"
    fewresults = "Te weinig resultaten"
    encryption = "Encrypted"
    EOF = "EOF-Error"
    noresults = "Geen resultaten"
    nodocument = "Geen document"


def initialiseVariables(currentYear):
    global year
    year = currentYear

    global path
    path = "PDFs/{0}/All/".format(year)

    global organisationsList
    organisationsList = getOrganisationsList(year)

    global PDFsListRaw
    PDFsListRaw = getPDFsList(year)

    global PDFsListClean
    PDFsListClean = []
    for i in PDFsListRaw:
        PDFsListClean.append(i.split(".")[1].strip())

    global processedData
    processedData = Counter(PDFsListClean)

    global categories
    categories = []
    for searchterm in SearchTerm:
        categories.append(Category(searchterm.value))

    global totalPdfs
    totalPdfs = 0
    for item in processedData:
        itemAmount = processedData.get(item)
        totalPdfs += itemAmount

    global totalOrganisations
    totalOrganisations = len(os.listdir(path))


def categorise():
    global categories
    #: Create an empty matrix to pass through the initial matrixAtLeastOne() function
    matrix = createEmptyMatrix()

    #: Convert the un-indexable "SearchTerm Enum" into an indexable List
    searchTermList = [e for e in SearchTerm]
    searchTermListCount = len(searchTermList)

    #: Pass every searchTerm through the matrixAtLeastOne() checker
    #: To check if there is at least one Pdf in the organisation that meets the criteria
    #: This will determine in which category the organisation will be classified
    i = 0
    while i < searchTermListCount:
        #: Every searchTerm will use the matrix of the searchTerm before it
        #: AND every searchTerm will produce a more saturated matrix than the last
        #: This matrix is a list of zeroes that will be swapped to ones when the
        #: corresponding organisation has been categorised
        searchData = matrixAtLeastOne(matrix, searchTermList[i])
        matrix = searchData[0]
        categories[i].matrix = searchData[1]
        categories[i].amount = searchData[2]
        categories[i].organisations = searchData[3]
        i += 1


def matrixAtLeastOne(filledMatrix, searchTerm):
    #: This function creates the data necessary to categorise the organisations
    #: It is meant to be called recursively for each category like layers of a filter
    #: It's inputs are the binary list created by the last filter(filledMatrix), and the category name (searchTerm)
    #: It's outputs are;
    #: a binary list for the next filter,
    #: a binary list unique to this category,
    #: a count of occurences,
    #: and a list of pdf-map names of each organisations that belongs to that category
    global path
    global year
    global PDFsListClean
    global organisationsList
    #: Create variables for loop;
    #: - searchTermCount; for how often the searchterm occurs at least once in the available matrix
    #: - totalOrganisations; we loop through all available organisations
    #: - UniqueMatrix; is the matrix that will correspond to this specific category. It will only on have a '1' on
    #:   the places where an instance of an organisation belonging to this category is found
    searchTermCount = 0
    totalOrganisations = len(os.listdir(path))
    UniqueMatrix = createEmptyMatrix()
    UniqueOrganisationsList = []
    i = 0

    while i < totalOrganisations:
        if not filledMatrix[i]:
            #: If there is a 0 it means that organisation hasn't been categorised yet
            currentPDF = i*3
            if searchTerm.value in PDFsListClean[currentPDF:currentPDF + 3]:
                #: Check if this current searchTerm in one of the 3 Pdf's of organisation
                filledMatrix[i] = 1
                #: Fill in the filledMatrix; this org has been classified
                UniqueMatrix[i] = 1
                #: Fill in the uniqueMatrix; this is the classified organisation
                UniqueOrganisationsList.append(organisationsList[i])
                #: Add the organisation name to the UniqueOrganisationsList, will be saved in its corresponding category
                searchTermCount += 1
                #: Increment total found searches on this searchTerm
        i += 1

    return filledMatrix, UniqueMatrix, searchTermCount, UniqueOrganisationsList


def calculatePercentage(partial, total):
    percentage = str(round(100 * (partial / total), 2)) + "%"
    return percentage


def getPDFsList(year):
    #: Returns a list of all PDFs
    global path
    PDFsList = []
    pdfCounter = 0
    Path(path).mkdir(parents=True, exist_ok=True)

    for organisation in os.listdir(path):
        for pdf in os.listdir(path+organisation):
            pdfCounter += 1
            PDFsList.append(pdf)

    return PDFsList


def createEmptyMatrix():
    #: Returns a list of zeroes as large as the amount of organisations
    emptyMatrix = []
    i = 0
    while i < totalOrganisations:
        emptyMatrix.append(0)
        i += 1
    return emptyMatrix


def getOrganisationsList(year):
    #: Returns a list containing all organisation folder names
    #: Example: "PDFs\2020\All\7 - Afvalinzameling Land van Cuijk en Boekel"
    global path
    organisationsList = []
    organisationCounter = 0
    Path(path).mkdir(parents=True, exist_ok=True)

    for organisation in os.listdir(path):
            organisationCounter += 1
            organisationsList.append(organisation)

    return organisationsList


#def generatePdf():


def movePdfs(year):
    #: This function copies all pdfs from "All" and puts them into their own respective categories
    global categories
    for category in categories:
        for organisation in category.organisations:
            originalPath = "PDFs/{0}/All/{1}".format(year, organisation)
            newPath = "PDFs/{0}/{1}/{2}".format(year, category.name, organisation)
            Path(newPath).mkdir(parents=True, exist_ok=True)
            #: Move the entire organisation map to the new location
            copy_tree(originalPath, newPath)




if __name__ == '__main__':

    print(createRapport(2020))