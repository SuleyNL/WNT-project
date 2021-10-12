from enum import Enum


class Category:
    def __init__(self, name):
        self.name = name
        self.amount = 0
        self.matrix = []
        self.organisations = []


class Categories(Enum):
    succes = 0

    encryption = 1
    downloadError = 2
    nowords = 3
    EOF = 4

    noresults = 5
    fewresults = 6
    nodocument = 7


class Error(Enum):
    fewresultsError = "Geen WNT - Te weinig zoekresultaten"
    noresultsError = "Geen WNT - Geen zoekresultaten"
    downloadError = "Encrypted - Download error"
    encryptionError = "Encrypted - Standaard"
    EOFError = "Encrypted - EOF-Error"
    nowordsFoundError = "Encrypted - Geen woorden"
    nodocumentError = "Geen WNT - Geen document"


class SearchTerm(Enum):
    succes = "Wel WNT"

    encryption = "Encrypted - Standaard"
    EOF = "Encrypted - EOF-Error"
    downloadError = "Encrypted - Download error"
    nowords = "Encrypted - Geen woorden"

    noresults = "Geen WNT - Geen zoekresultaten"
    fewresults = "Geen WNT - Te weinig zoekresultaten"
    nodocument = "Geen WNT - Geen document"
