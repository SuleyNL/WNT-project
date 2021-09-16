import os
import math
import requests
from PyPDF2 import PdfFileReader, PdfFileWriter
from pathlib import Path
import pikepdf
from pdfminer.pdfpage import PDFPage
from reportlab.pdfgen.canvas import Canvas

def startProcess(year):
    global isError
    isError = False

    iteration = getIteration(year)
    organisation = getOrganisation(iteration)
    url = getUrl(iteration, year)
    pageNumber = 0
    if isFileDownloaded(url):
        pageNumber = getPageNumber()
    generateFile(pageNumber, year, organisation, iteration, url)
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


def getOrganisation(iteration):
    with open("WNT-List.txt") as file:
        organisation = file.readlines()[iteration[0]].replace("\n", "")

    return organisation


def getUrl(coordinates, year):
    url = ""

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
    totalScore = []

    if pdf.isEncrypted:
        try:
            pdf1 = pikepdf.open(pdf.pages)
            pdf.save(pdf1)
            #pdf = pdf.decrypt('')
        except NotImplementedError:
            print("errortje")
            # https://smallpdf.com/unlock-pdf

    while pageNumber < pdf.getNumPages():
        page = pdf.getPage(pageNumber).extractText().split(" ")

        if pageNumber == 6:
            print(str(page))

        relevanceScore = page.count("bezoldiging") + page.count("Bezoldiging") + page.count("BEZOLDIGING") + page.count("WNT")
        totalScore.append(relevanceScore)
        print(page.count("WNT"))

        pageNumber += 1


    # if there are no results for searchterm, activate error
    if sum(totalScore) == 0:
        print(totalScore)
        errorhandler("noresults")

    # Find the page number with the highest value
    pageNumber = totalScore.index(max(totalScore))

    return pageNumber


def errorhandler(errorText):
    global isError
    global error
    error = errorText
    if isError:
        isError = False
    else:
        isError = True


def generateFile(pageNumber, year, organisation, iteration, url):
    global isError
    global error
    if not isError:
        pages_to_keep = [pageNumber-1, pageNumber, pageNumber+1, pageNumber+2]
        infile = PdfFileReader("WorkingMemory/currentFile.pdf", 'rb')
        output = PdfFileWriter()

        for i in pages_to_keep:
            p = infile.getPage(i)
            output.addPage(p)

        # create path
        newPath = Path("PDFs/{0}/{1}/".format(year, organisation))
        newPath.mkdir(parents=True, exist_ok=True)
        # create file
        newFile = Path(str(newPath) + "/{0}.pdf".format(iteration[1]))
        with open(newFile, 'wb') as f:
            output.write(f)
    else:
        # create path
        newPath = Path("PDFs/{0}/{1}/".format(year, organisation))
        newPath.mkdir(parents=True, exist_ok=True)

        # create special error file
        newFile = str(newPath) + "/{0}.{1}.pdf".format(iteration[1], error)
        canvas = Canvas(newFile)
        canvas.drawString(5, 800, "Organisatie: ")
        canvas.drawString(5, 780, organisation)
        canvas.drawString(5, 740, "Link: ")
        canvas.drawString(5, 720, url)
        rect = Canvas.rect(canvas, 20, 700, 400, 20, 0)
        canvas.linkURL(url, rect)
        canvas.setFont("Helvetica", 15)
        canvas.save()


if __name__ == '__main__':

    print(startProcess(2020))