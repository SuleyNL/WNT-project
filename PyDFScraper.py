import os
import math
import requests
import time
import datetime
import PyPDF2
from PyPDF2 import PdfFileReader, PdfFileWriter, utils
from pathlib import Path
import pikepdf
from pdfminer.pdfpage import PDFPage
from reportlab.pdfgen.canvas import Canvas
from enum import Enum

def startProcess(year):
    global isError
    global report
    organisationAmount = getOrganisationAmount()
    iteration = getIteration(year)

    while iteration[0] < organisationAmount:
        #   the default setting is the best case scenario, will be modified if something is wrong.
        isError = False
        report = "Wel resultaten"

        iteration = getIteration(year)
        organisation = getOrganisation(iteration)
        url = getUrl(iteration, year)
        pageNumber = 0

        if not isError and isFileDownloaded(url):
            try:
                pageNumber = getPageNumber()
            except PyPDF2.utils.PdfReadError as e:
                errorhandler(Error.EOFError)

        generateFile(pageNumber, year, organisation, iteration, url)
    return "------[THE END]------"


class Error(Enum):
    noresultsError = "Geen resultaten"
    encryptionError = "Encrypted"
    EOFError = "EOF-Error"
    fewresultsError = "Te weinig resultaten"
    nodocumentError = "Geen document"


def errorhandler(error):
    global isError
    global report
    report = error.value
    isError = True


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
            errorhandler(Error.nodocumentError)
    return url


def isFileDownloaded(url):

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"}

    try:
        print("waiting up to 1 minute to download pdf from: %s" % url)
        response = requests.get(url, headers=headers, timeout=60)


        path = Path("WorkingMemory")
        path.mkdir(parents=True, exist_ok=True)

        with open("WorkingMemory/currentFile.pdf", "wb+") as file:
            file.write(response.content)

    except requests.exceptions.ConnectionError or UnboundLocalError:
        print("error: ")
        print("trying again")
        isFileDownloaded(url)
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
            # OCR is another alternative

    totalScore = []

    i = 0
    try:
        while i < pdf.getNumPages():
            page = pdf.getPage(i).extractText().split(" ")

            #relevanceScore = page.count("bezoldiging") + page.count("Bezoldiging") + page.count("BEZOLDIGING") + page.count("WNT")
            #print(item.count("bezoldiging") for item in page)
            highscore = 0
            currentScore =  sum((itm.count("bezoldiging") for itm in page)) + \
                            sum((itm.count("WNT") for itm in page)) + \
                            sum((itm.count("bezoldigingsmaximum") for itm in page)) + \
                            sum((itm.count("Wet Normering") for itm in page)) + \
                            sum((itm.count("Bezoldiging") for itm in page))

            totalScore.append(currentScore)
            if currentScore > highscore:
                highscore = currentScore
                pageNumber = highscore
            i += 1

    except:
        errorhandler(Error.encryptionError)

    # if there are no results for searchterm, report an error
    if sum(totalScore) < 1:
        errorhandler(Error.noresultsError)
    elif sum(totalScore) < 4:
        errorhandler(Error.fewresultsError)
    else:
        # Find the page number with the highest value
        pageNumber = totalScore.index(max(totalScore))
    print(totalScore)
    print(pageNumber)
    return pageNumber


def generateFile(pageNumber, year, organisation, iteration, url):
    global isError
    global report

    #   create the file
    newPath = Path("PDFs/{0}/{1}/".format(year, organisation))
    newPath.mkdir(parents=True, exist_ok=True)
    newFile = str(newPath) + "/{0}. {1}.pdf".format(iteration[1]+1, report)

    #   create the first page, with a report of found results
    canvas = Canvas(newFile)
    errorText = report

    canvas.drawString(20, 800, "Dit document heeft:")
    canvas.drawString(180, 800, str(errorText))

    canvas.drawString(20, 760, "Organisatie: ")
    canvas.drawString(180, 760, organisation)

    getMonthName = ["Januari",
                     "Februari",
                     "Maart",
                     "April",
                     "Mei",
                     "Juni",
                     "Juli",
                     "Augustus",
                     "September",
                     "Oktober",
                     "November",
                     "December"]
    today = datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d")

    canvas.drawString(20, 720, "Moment van scraping: ")
    canvas.drawString(180, 720, str(today.day) + " " + getMonthName[today.month-1] + " " + str(today.year))

    canvas.drawString(20, 700, "")
    canvas.drawString(180, 700, str(format(datetime.datetime.now(), '%H:%M:%S')))

    canvas.drawString(20, 680, "Link: ")
    canvas.drawString(20, 660, url)
    rect = Canvas.rect(canvas, 20, 700, 400, 20, 0)
    canvas.linkURL(url, rect)

    canvas.setFont("Helvetica", 11)
    canvas.save()

    # if there is no error: we have located the relevant pages and can store them in this pdf
    if not isError:
        pages_to_keep = [pageNumber-1, pageNumber, pageNumber+1, pageNumber+2]
        infile = PdfFileReader("WorkingMemory/currentFile.pdf", 'rb')
        output = PdfFileWriter()

        reportpage = PdfFileReader(newFile, 'rb').getPage(0)
        output.addPage(reportpage)
        for i in pages_to_keep:
            p = infile.getPage(i)
            output.addPage(p)

        with open(newFile, 'wb') as f:
            output.write(f)


if __name__ == '__main__':

    print(startProcess(2020))