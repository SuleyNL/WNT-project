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

def startProcess(year):
    PDFsList = getPDFsList(2020)
    hashmap = Counter(PDFsList)
    noresultsCounter = 0
    resultsCounter = 0
    for i in hashmap:
        if i.endswith("noresults.pdf"):
            noresultsCounter += hashmap.get(i)

        if i.endswith(".pdf"):
            resultsCounter = resultsCounter + hashmap.get(i)

        else:
            print(i + ":  " + str(hashmap.get(i)))

    print("results: " + ":  " + str(resultsCounter))
    print("noresults: " + ":  " + str(noresultsCounter))

    print("percentage of noresults: " + str((round(noresultsCounter/resultsCounter, 3))*100) + "%")
    return "------[THE END]------"


def getPDFsList(year):
    coordinates = [0, 0]
    PDFsList = []
    path = "PDFs/%s/" %year
    pdfCounter = 0
    Path(path).mkdir(parents=True, exist_ok=True)

    for organisation in os.listdir(path):
        for pdf in os.listdir(path+organisation):
            pdfCounter += 1
            PDFsList.append(pdf)

    return PDFsList


if __name__ == '__main__':

    print(startProcess(2020))