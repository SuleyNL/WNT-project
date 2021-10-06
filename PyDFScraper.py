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
import warnings


def startProcess(year):
    global isError
    global report
    organisationAmount = getOrganisationAmount()
    iteration = getIteration(year)

    while iteration[0]+1 <= organisationAmount:
        print(str(iteration[0]))
        print(organisationAmount)

        #   the default setting is the best case scenario, will be modified if something is wrong.
        isError = False
        report = "Wel resultaten"
        try:
            iteration = getIteration(year)
            organisation = getOrganisation(iteration)
        except IndexError:
            break
        url = getUrl(iteration, year)
        pageNumber = 0

        if not isError and isFileDownloaded(url):
            try:
                if isEncrypted():
                    errorhandler(Error.encryptionError)
                else:
                    pageNumber = getPageNumber()

            except PyPDF2.utils.PdfReadError as e:
                errorhandler(Error.EOFError)

        generateFile(pageNumber, year, organisation, iteration, url)
        print("Processed {0} organisations and {1} files".format(iteration[0]+1, ((iteration[0]-1)*3)+iteration[1]))
        newPath = Path("PDFs/{0}/All/{1}/".format(year, organisation))

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

    path = "PDFs/{0}/All/".format(year)
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
    # filename.mkdir(parents=True, exist_ok=True)

    with open("URLs-List/URLs-List-%s.txt" % year) as file:
        line = file.readlines()[coordinates[0]].split(":")
        line.remove(line[0])

        urlList = ":".join(line).split(", ")

        #: if the current iteration (goes from 0,1,2) is smaller than the amount of urls in the line (could be 0,1,2,3)
        #: that means we can get a document
        #: else we raise nodocumentError
        if coordinates[1] < len(urlList):
                url = ":".join(line).split(", ")[coordinates[1]].strip()
        else:
            errorhandler(Error.nodocumentError)
    return url


def isFileDownloaded(url):

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"}
    i = 0
    while i < 10:
        # try to download file to workingmemory
        try:
            print("waiting up to 1 minute to download pdf from: {0}".format(url))
            response = requests.get(url, headers=headers, timeout=60)
            path = Path("WorkingMemory")
            path.mkdir(parents=True, exist_ok=True)
            with open("WorkingMemory/currentFile.pdf", "wb+") as file:
                file.write(response.content)
            return True
        # if connection is lost, we wait and try gain
        except requests.exceptions.ConnectionError:
            print("error: connectionerror")
            print("sleeping {0} sec then trying again".format((i+1)*10))
            time.sleep((i+1)*10)
            i += 1
            break
        except UnboundLocalError:
            print("error: unboundlocal error")
            print("trying again")
            i += 1
            break
        except requests.exceptions.MissingSchema:
            print("error: Missing url")
            errorhandler(Error.nodocumentError)
            break
    return False


def isEncrypted():
    pdf = PdfFileReader("WorkingMemory/currentFile.pdf")

    if pdf.isEncrypted:
    # if it is encrypted, try to decrypt it
        try:
            pdf1 = pikepdf.open("WorkingMemory/currentFile.pdf", allow_overwriting_input=True)
            pdf1.save('WorkingMemory/currentFile.pdf')
            pdf1.close()

            EOF_MARKER = b'%%EOF'

            mainfile = "WorkingMemory/currentFile.pdf"
            temporaryfile = "WorkingMemory/temporaryfile.pdf"
            with open(mainfile, 'rb') as f:
                contents = f.read()
                
                # check if EOF is somewhere else in the file
                if EOF_MARKER in contents:
                    # we can remove the early %%EOF and put it at the end of the file
                    contents = contents.replace(EOF_MARKER, b'')
                    contents = contents + EOF_MARKER
                else:
                    # Some files really don't have an EOF marker
                    # In this case it helped to manually review the end of the file
                    print(contents[-8:])  # see last characters at the end of the file
                    # printed b'\n%%EO%E'
                    contents = contents + EOF_MARKER

                with open(temporaryfile, 'wb') as g:
                    g.write(contents)

                infile = PdfFileReader(temporaryfile, False)
                output = PdfFileWriter()

                i = 0
                while i < infile.getNumPages():
                    p = infile.getPage(i)
                    output.addPage(p)
                    i += 1

                with open(mainfile, 'wb') as h:
                    output.write(h)


        except:
            return True
            print("errortje")
            # https://smallpdf.com/unlock-pdf is an alternate method for decryption
            # OCR is another alternative
    # if it is still encrypted, return true, else return false

    if pdf.isEncrypted:
        return True
    else:
        return False


def getPageNumber():
    pageNumber = 0
    pdf = PdfFileReader("WorkingMemory/currentFile.pdf")

    totalScore = []

    i = 0
    try:
        # For every page, check the amount of occurences of these searchterms
        while i < pdf.getNumPages():
            page = pdf.getPage(i).extractText().split(" ")

            #relevanceScore = page.count("bezoldiging") + page.count("Bezoldiging") + page.count("BEZOLDIGING") + page.count("WNT")
            highscore = 0
            currentScore = sum((itm.count("bezoldiging") for itm in page)) + \
                            sum((itm.count("WNT") for itm in page)) + \
                            sum((itm.count("bezoldigingsmaximum") for itm in page)) + \
                            sum((itm.count("Wet Normering") for itm in page)) + \
                            sum((itm.count("Bezoldiging") for itm in page))

            totalScore.append(currentScore)
            if currentScore > highscore:
                highscore = currentScore
                pageNumber = highscore
            i += 1
            print(str(pdf.getNumPages()-i))
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
    print("Relevance score matrix: \n" + str(totalScore))
    print("Relevant page: " + str(pageNumber))
    return pageNumber


def generateFile(pageNumber, year, organisation, iteration, url):
    global isError
    global report

    #   create the file
    newPath = Path("PDFs/{0}/All/{1} - {2}/".format(year, iteration[0], organisation))
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

    with open("WorkingMemory/currentFile.pdf", 'rb') as f:
        contents = f.read()
        rawdata1 = contents[:50]
        rawdata2 = contents[50:100]
        rawdata3 = contents[-100:-50]
        rawdata4 = contents[-50:-1]

    canvas.drawString(20, 620, "Eerste 100 bytes: ")
    canvas.drawString(20, 600, str(rawdata1))
    canvas.drawString(20, 580, str(rawdata2))

    canvas.drawString(20, 550, "Laatste 100 bytes: ")
    canvas.drawString(20, 530, str(rawdata3))
    canvas.drawString(20, 510, str(rawdata4))

    canvas.drawString(20, 480, "ID: ")
    canvas.drawString(180, 480, "Organisatie: " + str(iteration[0]+1) + ", Document: " +str(iteration[1]+1))

    canvas.setFont("Helvetica", 11)
    canvas.save()

    #: if there is no error: we have located the relevant pages and can store them in this pdf
    if not isError:
        #: Sometimes a pdf with a EOF-Error still gets through, we catch it with this try-block
        try:
            infile = PdfFileReader("WorkingMemory/currentFile.pdf", strict=False)
        except PyPDF2.utils.PdfReadError:
            #: if there is an EOF-error 'isError' will be set to True in the errorhandler
            errorhandler(Error.EOFError)

        if not isError:
            output = PdfFileWriter()
            i = pageNumber-1

            # first add the generated report to the new pdf file
            reportPage = PdfFileReader(newFile, 'rb').getPage(0)
            output.addPage(reportPage)

            # then check if there is pages left to add, starting at one before the main page, up to 4
            j = 0
            print(i)
            while i < infile.getNumPages() and j < 4:
                p = infile.getPage(i)
                output.addPage(p)
                i += 1
                j += 1

            with open(newFile, 'wb') as f:
                output.write(f)



if __name__ == '__main__':

    print(startProcess(2020))