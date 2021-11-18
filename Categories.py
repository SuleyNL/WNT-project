from enum import Enum


CategoryNames = {
    "Wel WNT": 0,
    "Encrypted - Standaard": 1,
    "Encrypted - EOF-Error": 2,
    "Encrypted - Download error": 3,
    "Encrypted - Geen woorden": 4,
    "Geen WNT - Geen zoekresultaten": 5,
    "Geen WNT - Te weinig zoekresultaten": 6,
    "Geen WNT - Geen document": 7
}


class Category:
    def __init__(self, name, id):
        self.name = name
        self.id = id

        self.filledMatrix = []
        self.UniqueMatrix = []
        self.searchTermCount = 0
        self.UniqueOrganisationsList = []


class Categories:

    def __init__(self):
        global CategoryNames
        self.categories = []
        i = 0
        while i < CategoryNames.__len__():
            self.categories.append(Category(list(CategoryNames.keys())[i], i))
            i += 1

    def get_all_categories(self):
        return self.categories

    def get_category_by_id(self, category_id: int):
        return self.categories[category_id]

    def get_category_by_name(self, category_name: str):
        return self.categories[CategoryNames[category_name]]

    def set_category(self, category: Category):
        self.categories[category.id] = category

    def set_data(self, filledMatrix, UniqueMatrix, searchTermCount, UniqueOrganisationsList, category_id):
        self.categories[category_id].filledMatrix = filledMatrix
        self.categories[category_id].UniqueMatrix = UniqueMatrix
        self.categories[category_id].searchTermCount = searchTermCount
        self.categories[category_id].UniqueOrganisationsList = UniqueOrganisationsList
        print(self.categories[category_id].UniqueOrganisationsList)


class Error(Enum):
    fewresultsError = "Geen WNT - Te weinig zoekresultaten"
    noresultsError = "Geen WNT - Geen zoekresultaten"
    downloadError = "Encrypted - Download error"
    encryptionError = "Encrypted - Standaard"
    EOFError = "Encrypted - EOF-Error"
    nowordsFoundError = "Encrypted - Geen woorden"
    nodocumentError = "Geen WNT - Geen document"


