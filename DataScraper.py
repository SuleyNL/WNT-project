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


def createRapport(year):
    global categories
    global totalOrganisations
    #: Initialise all variables
    initialiseVariables(year)

    #: Categorise all organisations into the different search categories:
    #: [Wel resultaten,
    #:  Te weinig resultaten,
    #:  Encrypted,
    #:  EOF-Error,
    #:  Geen resultaten,
    #:  Geen document]
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

    #print()
    print(totalOrganisations)
    #print(categories[2].name)
    #print(categories[2].organisations)

    return "------[THE END]------"


class Category:
    def __init__(self, name):
        self.name = name
        self.count = 0
        self.matrix = []
        self.organisations = []


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

    global path
    path = "PDFs/{0}/".format(year)

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
    #: Create an empty matrix to pass through the initial matrixAtLeastOne() method
    matrix = createEmptyMatrix()

    #: Convert the un-indexable SearchTerm Enum into an indexable List
    searchTermList = [e for e in SearchTerm]
    searchTermListCount = len(searchTermList)

    #: Pass every searchTerm through the matrixAtLeastOne() checker
    #: To check if there is at least one Pdf in the organisation that meets the criteria
    #: This will determine in which classification the organisation goes
    i = 0
    while i < searchTermListCount:
        #: Every searchTerm will produce a more saturated matrix
        #: Every searchTerm will use the matrix of the searchTerm before it
        searchData = matrixAtLeastOne(matrix, searchTermList[i])
        matrix = searchData[0]
        categories[i].matrix = searchData[1]
        categories[i].amount = searchData[2]
        categories[i].organisations = searchData[3]
        i += 1


def matrixAtLeastOne(filledMatrix, searchTerm):
    global path
    global year
    global PDFsListClean
    global organisationsList
    #: Create variables for loop;
    #: - searchTermCount for how often the searchterm occurs at least once in the available matrix
    #: - totalOrganisations we loop through all available organisations
    #: - UniqueMatrix is the matrix that will correspond to this specific category. It will only on have a '1' on
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
                #: Add the organisation name to the UniqueOrganisationsList, this will be saved in its corresponding category
                searchTermCount += 1
                #: Increment total found searches on this searchTerm
        i += 1

    return filledMatrix, UniqueMatrix, searchTermCount, UniqueOrganisationsList


def calculatePercentage(partial, total):
    #: calculates the percentage of organisations in each category
    percentage = str(round(100 * (partial / total))) + "%"
    return percentage


def getPDFsList(year):
    PDFsList = []
    path = "PDFs/%s/" % year
    pdfCounter = 0
    Path(path).mkdir(parents=True, exist_ok=True)

    for organisation in os.listdir(path):
        for pdf in os.listdir(path+organisation):
            pdfCounter += 1
            PDFsList.append(pdf)

    return PDFsList


def createEmptyMatrix():
    emptyMatrix = []
    i = 0
    while i < totalOrganisations:
        emptyMatrix.append(0)
        i += 1
    return emptyMatrix


def getOrganisationsList(year):
    organisationsList = []
    path = "PDFs/%s/" % year
    organisationCounter = 0
    Path(path).mkdir(parents=True, exist_ok=True)

    for organisation in os.listdir(path):
            organisationCounter += 1
            organisationsList.append(organisation)

    return organisationsList


if __name__ == '__main__':

    print(createRapport(2020))