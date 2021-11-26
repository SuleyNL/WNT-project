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
from Categories import Error
import Categories
import warnings
import DataAnalyzer
import re
import struct

# Final pre- refactored version, 26-11-2021, 14:14
# NonFinal refactored version, 14:33

def startProcess(year: int):
    """
    Start of process.
    For every organisation, Process its PDFs

    After the loop, retry the failed PDFs once
    :type year: int
    :rtype: String
    """
    global isError
    global report
    organisationAmount = getOrganisationAmount()
    iteration = getIteration(year)

    while iteration[0]+1 <= organisationAmount:
        print("current organisation id: " + str(iteration[0]))
        organisation = getOrganisation(iteration)
        processPDF(year, organisation, iteration)
        #: Determine the next PDF
        iteration = getIteration(year)

    retryFailedPDFs(year)
    return "------[THE END]------"


def processPDF(year, organisation, iteration):
    """
    Manages the process of selection, downloading and decryption of a pdf
    and creation of a report file about that pdf
    Requires organisations' URL from PDF-URLs-List-{year}.txt

    :type year: int
    :type organisation: str
    :type iteration: list
    :rtype: None
    """

    global isError
    global report

    #: The default setting is the best case scenario, will be modified if something is wrong.
    isError = False
    report = "Wel WNT"
    pageNumber = 0

    #: Get the url of the PDF
    url = getUrl(iteration, year)
    downloadFile(url)

    if not isError:
        is_encrypted = isEncrypted()
        if is_encrypted == 1:
            errorhandler(Error.encryptionError)
        elif is_encrypted == 2:
            errorhandler(Error.EOFError)
        else:
            try:
                pageNumber = getPageNumber()
            except PyPDF2.utils.PdfReadError as e:
                errorhandler(Error.EOFError)
    print(organisation)
    generateFile(pageNumber, year, organisation, iteration, url)
    print("Processed {0} organisations and {1} files".format(iteration[0]+1, ((iteration[0] - 1) * 3) + iteration[1]+4))
    print(str(math.floor((iteration[0]+1)*100/1889)) + "% DONE")
    # newPath = Path("PDFs/{0}/All/{1}/".format(year, organisation))


def errorhandler(error):
    """
    Manages the handling of errors

    When called, changes isError to True and updates report to be the error classification
    This will be used in the generated PDF

    :type error: Categories.Error
    :rtype: None
    """
    global isError
    global report
    report = error.value
    isError = True


def getIteration(year):
    """
    Determines the next up organisation and file

    Stores this information in 2 ID's
    The first is the ID of the organisation - coordinates[0]
    The second is the ID of the PDF - coordinates[1]

    :type year: int
    :rtype coordinates: list
    """
    coordinates = [0, 0]

    path = "PDFs/{0}/All/".format(year)
    pdfCounter = 0
    organisationDirectory = path + str(coordinates[0]) + " - " + getOrganisation(coordinates)
    organisationAmount = getOrganisationAmount()
    Path(path).mkdir(parents=True, exist_ok=True)

    while coordinates[0] < organisationAmount:
        Path(organisationDirectory).mkdir(parents=True, exist_ok=True)
        if len(os.listdir(organisationDirectory)) == 3:
            #: Parse through all the orgs that have precisely 3 Pdfs, and count those in pdfCounter
            pdfCounter += len(os.listdir(organisationDirectory))
            coordinates = [math.floor(pdfCounter / 3), pdfCounter % 3]
            organisationDirectory = path + str(coordinates[0]) + " - " + getOrganisation(coordinates)
        else:
            break
        # Once out of the while loop, we have either reached the end of organisations
        # or we have found the organisation that misses a pdf

    pdfNames = []
    for org in os.listdir(organisationDirectory):
        pdfNames.append(org.split(".")[0])

    for i in range(1, 4):
            if str(i)in pdfNames:
                    print("Het getal {0} is in org".format(i))
            else:
                print("Het getal {0} is niet in org".format(i))
                coordinates[1] = i-1
                return coordinates
    else:
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

    return organisation


def getUrl(coordinates, year):
    """
    Gets the year and coordinates and uses those to lookup in PDF-URLs-List-{year}.txt to find the correlating url
    :returns url

    :type coordinates: str
    :type year: int
    :rtype: str
    """
    url = ""
    # if it doesnt create the file
    # filename.mkdir(parents=True, exist_ok=True)

    with open("PDF-URLs-List/PDF-URLs-List-%s-first.txt" % year) as file:
        line = file.readlines()[coordinates[0]].split(":")
        line.remove(line[0])
        if '' in line:
            line.remove('')
        urlList = ":".join(line).strip(' ')
        urlList = urlList.replace(" ", ", ").split(", ")

        #: if the current iteration (goes from 0,1,2) is smaller than the amount of urls in the line (could be 0,1,2,3)
        #: that means we can get a document
        #: else we raise nodocumentError
        if coordinates[1] < len(urlList):
                url = urlList[coordinates[1]].strip().strip(",")
        else:
            errorhandler(Error.nodocumentError)
    return url


def downloadFile(url):
    """
    Manages the downloading of a file from a url to WorkingMemory/currentFile.pdf
    Requires organisations' URL from PDF-URLs-List-{year}.txt

    :raises: Error.downloadError
    :type url: str
    :rtype: bool
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"}
    i = 0
    while i < 3:
        # try to download file to WorkingMemory
        try:
            print("waiting up to 1 minute to download pdf from: {0}".format(url))
            response = requests.get(url, headers=headers, timeout=60)
            path = Path("WorkingMemory")
            path.mkdir(parents=True, exist_ok=True)
            with open("WorkingMemory/currentFile.pdf", "wb+") as file:
                file.write(response.content)

            return True
        # if connection is lost, we wait and try gain
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectTimeout):
            print("error: connectionerror")
            print("sleeping {0} sec then trying again".format((i+1)*3))
            time.sleep((i+1)*3)
            i += 1
        except UnboundLocalError:
            print("error: unboundlocal error")
            print("trying again")
            time.sleep(1)
            i += 1
        except requests.exceptions.ReadTimeout:
            print("error: readtimeout error")
            print("trying again")
            time.sleep(1)
            i += 1
        except requests.exceptions.MissingSchema:
            print("error: Missing url")
            i += 1000
            break
    #: the while loop is supposed to return True or break.
    errorhandler(Error.downloadError)
    return False


def decryptFile(decryptionMethod: int, currentfile: str):
    FAILED_EOF_MARKER = b'%%EO'
    EOF_MARKER = b'%%EOF'
    decryptedfile = "WorkingMemory/decryptedfile.pdf"
    with open(currentfile, 'rb') as file:
        contents = file.read()
        listcontents = file.readlines()
    '''
        #: Only for testing purposes:
        #: Comment this out if you run the program
    with open("WorkingMemory/bytes.txt", 'wb+') as g:
        g.write("this organisation".encode('utf-8') + "\n".encode('utf-8')
                + report.encode('utf-8') + "\n".encode('utf-8')
                + contents)
    '''
    if decryptionMethod == 0:
        #: METHOD 0
        #: Check if there is a PDF in the first place
        try:
            pdf = PdfFileReader(currentfile, strict=False)
        except PyPDF2.utils.PdfReadError:
            errorhandler(Error.EOFError)
            # Most of cases when we land in this exception its because the PDF is embedded in a PDF Viewer
            # We could possibly create another errortype for this kind of error: Embedded PDF Viewer Error
            # TODO: Create a way to download from pdf embedded in webviewers

    if decryptionMethod == 1:
        #: METHOD 1
        #: Decrypting using PyDF and an empty password
        try:
            pdf = PdfFileReader(currentfile, strict=False)
            pdf.decrypt('')
        except (KeyError, NotImplementedError, struct.error):
            pass

    elif decryptionMethod == 2:
        #: METHOD 2
        #: Decrypting using qpdf and an empty password
        # TODO: TRANSLATE THIS COMMAND FROM LINUX TO WINDOWS
        #command = "copy \"WorkingMemory\\currentFile.pdf\" \"WorkingMemory\\temp.pdf\"; qpdf --password='' --decryptFile \"WorkingMemory\\temp.pdf\" \"WorkingMemory\\currentFile.pdf\""
        #command = "copy " + currentfile + " WorkingMemory/temp.pdf; qpdf --password='' --decryptFile temp.pdf " + currentfile
        #os.system(command)
        pass

    elif decryptionMethod == 3:
        #: METHOD 3
        #: Decrypting using pikepdf
        try:
            pdf1 = pikepdf.open(currentfile, allow_overwriting_input=True)
            pdf1.save(currentfile)
            pdf1.close()
        except (pikepdf._qpdf.PdfError, pikepdf._qpdf.DataDecodingError):
            pass

    elif decryptionMethod == 4:
        #: METHOD 4
        #: we can replace the %%EO for an %%EOF
        if EOF_MARKER not in contents and FAILED_EOF_MARKER in contents:
            newcontents = contents.replace(FAILED_EOF_MARKER, EOF_MARKER)
            with open(currentfile, 'wb+') as g:
                g.write(newcontents)

    elif decryptionMethod == 5:
        #: METHOD 5
        #: Remove HTML from end of file
        if EOF_MARKER in contents:
            newcontents = removeHTMLfromPDF(listcontents, contents)
            # only write the new contents to file if it has contents, because it can fail and produce an empty list
            if len(newcontents) > 1:
                with open(currentfile, 'wb+') as h:
                    h.writelines(newcontents)

    elif decryptionMethod == 6:
        #: METHOD 6
        #: we can remove the early %%EOF and put it at the end of the file
        if EOF_MARKER in contents:
            contents = contents.replace(EOF_MARKER, b'')
            newcontents = contents + EOF_MARKER
            with open(currentfile, 'wb+') as h:
                h.write(newcontents)

    elif decryptionMethod == 7:
        #: METHOD 7
        #: Force the EOF marker to stay at the end of the file
        if EOF_MARKER in contents[-10:]:
            pass
        elif EOF_MARKER in contents:
            actual_line = len(contents) - 1
            for i, x in enumerate(contents[::-1]):
                try:
                    iterator = iter(x)
                    print("iterable")
                except TypeError:
                    break
                else:
                    if b'%%EOF' in x:
                        actual_line = len(contents) - i - 1
                        break
            newcontents = contents[:actual_line +1] + b'%%EOF'
            with open(currentfile, 'wb') as f:
                f.writelines(newcontents)

    elif decryptionMethod == 8:
        #: METHOD 8
        #: Some files really don't have an EOF marker
        # In this case it helped to manually review the end of the file
        # print(contents[-8:])  # to see last characters at the end of the file
        # printed b'\n%%EO%E'
        # So we manually add it to the file
        if EOF_MARKER not in contents:
            newcontents = contents + EOF_MARKER
            with open(currentfile, 'wb+') as g:
                g.write(newcontents)
    '''
    infile = PdfFileReader(decryptedfile, strict=False)
    output = PdfFileWriter()

    i = 0
    while i < infile.getNumPages():
        p = infile.getPage(i)
        output.addPage(p)
        i += 1

    with open(currentfile, 'wb') as h:
        output.write(h)
    '''
    return currentfile


def isEncrypted():
    """
    Manages the decryption process of a PDF in WorkingMemory/currentFile.pdf

    Checks if file is encrypted and then tries 8 methods of decryption
    Then stores it in WorkingMemory/decryptedfile.pdf
    if after all tries the file is still encrypted then return False
    :rtype: int
    """
    global isError
    currentfile = "WorkingMemory/currentFile.pdf"
    # https://stackoverflow.com/questions/26242952/pypdf-2-decrypt-not-working
    decryptionMethod = 0

    while decryptionMethod < 9 and not isError:
        decryptFile(decryptionMethod, currentfile)
        decryptionMethod +=1
    try:
        pdf = PdfFileReader(open(currentfile, "rb"))
        if not pdf.isEncrypted:
            return 0
        else:
            return 1
    except (TypeError, ValueError, PyPDF2.utils.PdfReadError):
        return 2


def removeHTMLfromPDF(pdf_stream_in: list, contents: bytes):
    """
    Is supposed to remove all remains of html from the end of the byte-file

    :type pdf_stream_in: list
    :type contents: bytes
    :rtype: list
    """
    # find the line position of the EOF
    for i, x in enumerate(contents[::-1]):
        actual_line = len(pdf_stream_in) - i
        try:
            iterator = iter(x)
            print("iterable")
        except TypeError:
            break
        else:
            if b'%%EOF' in x:
                actual_line = len(pdf_stream_in) - i
                print(f'EOF found at line position {-i} = actual {actual_line}, with value {x}')
                break
    # return the list up to that point
    return pdf_stream_in[:actual_line]


def getPageNumber():
    """
    Manages the process of page selection.

    Checks the sum of all keywords found in each page of the pdf
    Also checks the sum of natural words found in each page of the pdf
    if the sum of natural words is less than threshold value, raise nowordsfoundError
    Returns the page number containing the highest count

    realWordScore is on average ~20
    threshold is set at 4

    :rtype: int
    """
    pageNumber = 0
    pdf = PdfFileReader("WorkingMemory/currentFile.pdf", strict=False)

    totalScore = []
    realWordScore = 0
    i = 0
    try:
        # For every page, check the amount of occurences of these searchterms
        while i < pdf.getNumPages():
            page = pdf.getPage(i).extractText().split(" ")
            realWordScore += sum((itm.lower().count("de") for itm in page))
            #relevanceScore = page.count("bezoldiging") + page.count("Bezoldiging") + page.count("BEZOLDIGING") + page.count("WNT")
            highscore = 0
            currentScore = sum((itm.lower().count("bezoldiging") for itm in page)) + \
                            sum((itm.lower().count("topfunctionarissen") for itm in page)) + \
                            sum((itm.lower().count("bezoldigingdmaximum") for itm in page)) + \
                            sum((itm.lower().count("wnt") for itm in page))

            totalScore.append(currentScore)
            if currentScore > highscore:
                highscore = currentScore
                pageNumber = highscore
            i += 1
    except Exception as e:
        print(e)
        errorhandler(Error.encryptionError)

    #: if no real words have been found, report encryption
    #: "de " occurs on average 20 times per page, threshold will be set at the low end of 4 occurrences per page
    if pdf.getNumPages() == 0:
        errorhandler(Error.downloadError)
    elif realWordScore/pdf.getNumPages() < 4:
        errorhandler(Error.nowordsFoundError)
    # if there are no results for searchterm, report an error
    elif sum(totalScore) < 1:
        errorhandler(Error.noresultsError)
    elif sum(totalScore) < 4:
        errorhandler(Error.fewresultsError)
    else:
        # Find the page number with the highest value
        pageNumber = totalScore.index(max(totalScore))
    print("Relevance score matrix: \n" + str(totalScore))
    print("Relevant page: " + str(pageNumber))
    print("RealWordScore: " + str(realWordScore))
    return pageNumber


def generateFile(pageNumber, year, organisation, iteration, url):
    """
    Manages the creation of a report file

    :type pageNumber: int
    :type year: int
    :type organisation: str
    :type iteration: list
    :type url: str

    :rtype: None
    """
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
        rawdata4 = contents[-50:]

    '''
        #: Only for testing purposes:
        #: Comment this out if you run the program   
    with open("WorkingMemory/bytes.txt", 'wb+') as g:
        g.write(organisation.encode('utf-8') + "\n".encode('utf-8')
                + report.encode('utf-8') + "\n".encode('utf-8')
                + contents)
    '''
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
            reportPage = PdfFileReader(newFile, strict=False).getPage(0)
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


def retryFailedPDFs(year):
    """
    Applies the processPDF() method on all PDFs that contain a DownloadError within given year

    :type year: int
    :rtype: None
    """
    path = "PDFs/{0}/All/".format(year)
    pdfCounter = 0
    iteration = [0, 0]
    organisationList = os.listdir(path)

    while iteration[0]+1 < len(organisationList):
        organisation = getOrganisation(iteration)
        organisationDirectory = os.listdir(path + str(iteration[0]) + " - " + organisation)
        for pdf in organisationDirectory:
            pdfCounter += 1
            print("pdfCounter: " + str(pdfCounter))

            if "Download error" in pdf:
                print(path + str(iteration[0]) + " - " + organisation + "/" + pdf)
                os.remove(path + str(iteration[0]) + " - " + organisation + "/" + pdf)
                print("iteration: " + (str(iteration)))
                print("organisation: " + organisation)
                #processPDF(year, organisation, iteration)

            iteration = [math.floor(pdfCounter / 3), pdfCounter % 3]


def cleanDoublesFromList(year):
    path = "PDFs/{0}/All/".format(year)
    organisationList = []
    for organisation in os.listdir(path):
        print(organisation)
        id = ''.join(organisation.split(" - ")[1:-1])
        if organisation not in organisationList:

            print(str(organisation) + "not in here")
            organisationList.append(organisation)
        else:
            print(str(organisation) + "in here")
            os.remove(organisation)
            print(organisation)


def deleteFolder(year):
    coordinates = [0, 0]

    path = "PDFs/{0}/All/".format(year)
    pdfCounter = 0
    Path(path).mkdir(parents=True, exist_ok=True)
    organisations = getOrganisationAmount()

    while coordinates[0] <= organisations:
        pdfsInOrg = 0
        print("pdfCOunter: " + str(pdfCounter))

        organisation = str(coordinates[0]) + " - " + getOrganisation(coordinates)
        print(path+organisation)
        try:
            for pdf in os.listdir(path+organisation):
                pdfCounter += 1
                pdfsInOrg += 1
            coordinates = [math.floor(pdfCounter / 3), pdfCounter % 3]

            if pdfsInOrg > 1:
                print("good")
            else:
                os.removedirs(path+organisation)
        except FileNotFoundError:
            print("done already")
            pdfCounter += 1
            coordinates = [math.floor(pdfCounter / 3), pdfCounter % 3]

    coordinates = [math.floor(pdfCounter/3), pdfCounter % 3]


if __name__ == '__main__':
    #retryFailedPDFs(2020)
    #cleanDoublesFromList(2020)
    print(startProcess(2020))
    #deleteFolder(2020)
