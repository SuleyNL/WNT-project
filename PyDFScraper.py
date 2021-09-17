import os
import math
import requests
import PyPDF2
from PyPDF2 import PdfFileReader, PdfFileWriter, utils
from pathlib import Path
import pikepdf
from pdfminer.pdfpage import PDFPage
from reportlab.pdfgen.canvas import Canvas

def startProcess(year):
    global isError
    isError = False
    organisationAmount = getOrganisationAmount()
    iteration = getIteration(year)

    while iteration[0] < organisationAmount:
        isError = False

        iteration = getIteration(year)
        organisation = getOrganisation(iteration)
        url = getUrl(iteration, year)
        pageNumber = 0

        if not isError and isFileDownloaded(url):
            try:
                pageNumber = getPageNumber()
            except PyPDF2.utils.PdfReadError as e:
                errorhandler(e)

        generateFile(pageNumber, year, organisation, iteration, url)

    return "------[THE END]------"


def getIteration(year):
    coordinates = [0, 0]

    path = "PDFs/%s/" %year
    pdfCounter = 0
    Path(path).mkdir(parents=True, exist_ok=True)

    for organisation in os.listdir(path):
        for pdf in os.listdir(path+organisation):
            pdfCounter += 1

    coordinates = [math.floor(pdfCounter/3), pdfCounter % 3]
    return coordinates


def getOrganisationAmount():
    with open("Extra/WNT-List.txt") as f:
        file = f.readlines()
        amountOfOrganisations = len(file)

    return amountOfOrganisations


def getOrganisation(iteration):
    with open("Extra/WNT-List.txt") as f:
        file = f.readlines()
        organisation = file[iteration[0]].replace("\n", "")
        amountOfOrganisations = len(file)

    return organisation


def getUrl(coordinates, year):
    url = ""
    # if it doesnt create the file
    #filename.mkdir(parents=True, exist_ok=True)

    with open("PDFs-List/PDFs-List-%s.txt" % year) as file:
        line = file.readlines()[coordinates[0]].split(":")
        line.remove(line[0])

        urlList = ":".join(line).split(", ")

        if not coordinates[1] == len(urlList):
            url = ":".join(line).split(", ")[coordinates[1]].strip()
        else:
            errorhandler("nodocument")
    return url


def isFileDownloaded(url):

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        isFileDownloaded(url)
        print("try again")
    path = Path("WorkingMemory")
    path.mkdir(parents=True, exist_ok=True)

    with open("WorkingMemory/currentFile.pdf", "wb+") as file:
        file.write(response.content)
    return True


def getPageNumber():
    pageNumber = 0
    pdf = PdfFileReader("WorkingMemory/currentFile.pdf")

    if pdf.isEncrypted:
        try:
            pdf1 = pikepdf.open("WorkingMemory/currentFile.pdf", allow_overwriting_input=True)
            pdf1.save()
            pdf1.close()
            #pdf = pdf.decrypt('')
        except NotImplementedError:
            print("errortje")
            # https://smallpdf.com/unlock-pdf is an alternate method for decryption

    totalScore = []

    try:
        while pageNumber < pdf.getNumPages():
            page = pdf.getPage(pageNumber).extractText().split(" ")

            #relevanceScore = page.count("bezoldiging") + page.count("Bezoldiging") + page.count("BEZOLDIGING") + page.count("WNT")
            #print(item.count("bezoldiging") for item in page)
            relevanceScore = sum((itm.count("bezoldiging") for itm in page)) + \
                             sum((itm.count("WNT") for itm in page)) + \
                             sum((itm.count("bezoldigingsmaximum") for itm in page)) + \
                             sum((itm.count("Wet Normering") for itm in page))

            totalScore.append(relevanceScore)

            pageNumber += 1
    except:
        errorhandler("encrypted")


    # if there are no results for searchterm, activate error
    if sum(totalScore) < 1:
        errorhandler("noresults")
    else:
        # Find the page number with the highest value
        pageNumber = totalScore.index(max(totalScore))
    print(totalScore)
    print(pageNumber)
    return pageNumber


def errorhandler(errorText):
    global isError
    global error
    error = errorText
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
        if error == "noresults":
            errorText = "geen resultaten"
        else:
            errorText = error
        canvas.drawString(20, 800, "Dit document heeft:")
        canvas.drawString(150, 800, str(errorText))
        canvas.drawString(20, 760, "Organisatie: ")
        canvas.drawString(150, 760, organisation)
        canvas.drawString(20, 720, "Link: ")
        canvas.drawString(20, 700, url)
        rect = Canvas.rect(canvas, 20, 700, 400, 20, 0)
        canvas.linkURL(url, rect)
        canvas.setFont("Helvetica", 11)
        canvas.save()

if __name__ == '__main__':

    print(startProcess(2020))