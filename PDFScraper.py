import os
import math
import requests
from PyPDF2 import PdfFileReader, PdfFileWriter
from pathlib import Path

def startProcess(year):
    iteration = getIteration(year)
    url = getUrl(iteration, year)
    pageNumber = 0
    if isFileDownloaded(url):
        pageNumber = getPageNumber()
    generateFile(pageNumber)
    return "------[THE END]------"


def getIteration(year):
    coordinates = [0, 0]

    path = "PDFs/%s/" %year
    pdfCounter = 0
    for organisation in os.listdir(path):
        for pdf in os.listdir(path+organisation):
            pdfCounter += 1

    coordinates = [math.floor(pdfCounter/3), pdfCounter % 3]
    return coordinates


def getUrl(coordinates, year):
    url = ""
    with open("WNT-List.txt") as file:
        organisation = file.readline()[coordinates[0]]

    # if it doesnt create the file
    #filename.mkdir(parents=True, exist_ok=True)

    with open("PDFs-List/PDFs-List-%s.txt" % year) as file:
        line = file.readlines()[coordinates[0]].split(":")
        line.remove(line[0])
        url = ":".join(line).split(", ")[coordinates[1]].strip()
        print(url)
    return url


def isFileDownloaded(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"}
    response = requests.get(url, headers=headers)
    path = Path("WorkingMemory")
    path.mkdir(parents=True, exist_ok=True)

    with open("WorkingMemory/currentFile.pdf", "wb+") as file:
        file.write(response.content)
    return True


def getPageNumber():
    pageNumber = 0
    pdf = PdfFileReader("WorkingMemory/currentFile.pdf")
    for page in pdf.pages:
        print(page)
        if "jaar" in page:
            print("ja")
    return pageNumber


def generateFile(pageNumber):

    return ""


if __name__ == '__main__':
    print(startProcess(2020))