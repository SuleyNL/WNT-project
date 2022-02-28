import tabula
import pandas as pd
import math


def PdfDataMiningProcess(file):
    #file = "PDFs/2020/All/0 - ABG-organisatie/1. Wel WNT.pdf"
    tables = getTablesFromPDF(file)
    processedTables = {}
    i = 0
    for table in tables:
        category = categoriseTable(table)
        if category != 'Unknown':
            processedTable = processTable(category, table)
            processedTables.update({str(i) + ": " + category: processedTable})
            i += 1

    return processedTables


def getTablesFromPDF(file):
    '''
    in admin: cmd type:
    D:\School\Stage\Ministerie Binnenlandse Zaken\WNT-Project> python PdfDataMiner.py

    OR

    open Pycharm with admin rights to run this program
    :return: Pd.DataFrame
    :rtype:
    '''

    df = tabula.read_pdf(file, pages="all")

    return df


def categoriseTable(table: pd.DataFrame):
    hasKalenderjaar = False
    hasSubtotaal = False
    hasFunctionaris = False
    # gives a tuple of column name and series
    # for each column in the dataframe
    for (columnName, columnData) in table.iteritems():
        for word in columnData.values:
            word = str(word).lower().strip()
            if "kalenderjaar" in word:
                hasKalenderjaar = True
            elif "subtotaal" in word:
                hasSubtotaal = True
            elif "functionaris" in word:
                hasFunctionaris = True

    if hasKalenderjaar:
        return "Tabel1B"
    elif hasSubtotaal:
        return "Tabel1A"
    elif hasFunctionaris:
        return "Tabel1D"
    else:
        return "Unknown"


def processTable(category: str, table: pd.DataFrame):
    '''
    Gets any table and the category of that table, transforms the table based on which category it got.
    Then returns the table(s) without nan and without empty columns and with proper headings
    :param category: str
    :type category: str
    :param table: pd.DataFrame
    :type table: pd.DataFrame
    :return: Table
    :rtype: pd.DataFrame or List[pd.DataFrame, pd.DataFrame]
    '''
    outputTables = []
    if category == "Tabel1A":
        inputTables = splitUpperLowerTable(table)
        for table in inputTables:
            table = processTable1A(table)
            outputTables.append(table)

    elif category == "Tabel1B":
        outputTables.append(processTable1B(table))

    elif category == "Tabel1C":
        outputTables.append(processTable1C(table))

    elif category == "Tabel1D":
        outputTables.append(processTable1D(table))

    return outputTables


def processTable1A(table: pd.DataFrame):
    # The 'fieldsWithValues' are all the starting words in fields that are expected to contain values
    fieldsWithValues = ['bedragen',
                        'functiegegevens',
                        'aanvang',
                        'omvang',
                        'dienstbetrekking',
                        'beloning',
                        'beloningen',
                        'subtotaal',
                        'individueel',
                        '-/-',
                        'onverschuldigd ',
                        'bezoldiging',
                        'het',
                        'reden',
                        'toelichting']

    # The 'fieldsWithoutValues' are title fields, they do not contain values in the column
    fieldsWithoutValues = ['bezoldiging']

    # For every row in the first column,
    table.reset_index(level=0, drop=True, inplace=True)

    '''
    # Rename the Columns that are automatically categorised as 'Unnamed' to the names of Functionarissen
    for column in table.columns[1:]:
        if 'unnamed' in column.lower():
            table = table.rename(columns={column: table[column].iloc[0]})

    # Remove the Functionaris-Names because they have been moved to the column names
    table.drop(index=table.index[0],
            axis=0,
            inplace=True)
    '''

    i = 0
    while i < len(table.iloc[:, 0]):
        row = table.iloc[i, 0]

        # check if it is a fieldWithoutValue and if all values in it are NaN. If its the case, remove that row
        if any(fieldWithoutValues in str(row).lower() for fieldWithoutValues in fieldsWithoutValues):
            allisNaN = True

            for column in table.columns[1:]:
                if not isNaN(table[column][i]):
                    allisNaN = False

            if allisNaN:
                table.drop(index=i, inplace=True)
                table.reset_index(level=0, drop=True, inplace=True)
                i -= 1

        # else check if it contains no description. If it doesnt, unite with upper and lower row.
        elif isNaN(row):
            hasUpperNeighbour = False
            hasLowerNeighbour = False

            # if its not the first row, it has an upper neighbour
            if i != 0:
                hasUpperNeighbour = True
                upperNeighbour = table.iloc[i - 1, 0]

            # if its not the last row, it has a lower neighbour
            if i + 1 != len(table.iloc[:, 0]):
                hasLowerNeighbour = True
                lowerNeighbour = table.iloc[i + 1, 0]

            # if it has an upper neighbour, combine this row with that of its upper neighbour
            if hasUpperNeighbour:
                # the row_name should be that of its upper neighbour, since its current name is nan
                row_name = upperNeighbour
                new_row = {table.columns[0]: row_name}

                # Fill the new row up with the values that are present in the other columns
                for column in table.columns[1:]:
                    new_value = ""
                    # add upper row
                    if not isNaN(table[column].iloc[i - 1]):
                        new_value += table[column].iloc[i - 1] + " "
                    # add current row
                    if not isNaN(table[column].iloc[i]):
                        new_value += table[column].iloc[i]

                    new_row.update({column: new_value.strip()})
            # if it doesnt have an upper neighbour, combine this row with that of its lower neighbour
            else:
                row_name = ""
                if not isNaN(lowerNeighbour):
                    row_name += lowerNeighbour
                new_row = {table.columns[0]: row_name}

                # Fill the new row up with the values that are present in the other columns
                for column in table.columns[1:]:
                    new_value = ""
                    # add current row
                    if not isNaN(table[column].iloc[i]):
                        new_value += table[column].iloc[i] + " "
                    # add lower row
                    if not isNaN(table[column].iloc[i + 1]):
                        new_value += table[column].iloc[i + 1]

                    new_row.update({column: new_value.strip()})

            # Divide table in upper and lower half so that the new row can be inserted

            # if it has an upperNeighbour, take the upper half
            # else the upper half must be an empty dataframe
            if hasUpperNeighbour:
                upperHalf = table[:][:i - 1]
                lowerHalf = table[:][i + 1:]

            else:
                upperHalf = pd.DataFrame()
                lowerHalf = table[:][i + 2:]

            new_row = pd.DataFrame([new_row])
            i -= 1

            table = pd.concat([upperHalf, new_row, lowerHalf], ignore_index=True)
            table.reset_index(level=0, drop=True, inplace=True)

        # else check if it doesnt contain any of the starting words of fields with values,
        # if it doesnt, unite with upper row
        elif not any(fieldWithValue in str(row).split()[0].lower() for fieldWithValue in fieldsWithValues):

            upperNeighbour = table.iloc[i - 1, 0]
            new_row = {table.columns[0]: str(upperNeighbour) + " " + str(row)}

            for column in table.columns[1:]:
                new_value = ""

                if not isNaN(table[column].iloc[i]):
                    new_value += table[column].iloc[i] + " "

                if not isNaN(table[column].iloc[i - 1]):
                    new_value += table[column].iloc[i - 1]

            # Fill the new row up with the values that are present in the other columns
            for column in table.columns[1:]:
                new_row.update({column: new_value.strip(" ")})

            # Divide table in upper and lower half so that the new row can be inserted
            upperHalf = table[:][:i - 1]
            lowerHalf = table[:][i + 1:]
            new_row = pd.DataFrame([new_row])
            i -= 1

            table = pd.concat([upperHalf, new_row, lowerHalf], ignore_index=True)
            table.reset_index(level=0, drop=True, inplace=True)
        i += 1

    # Extract year from table
    jaar = table.columns[0].split(" ")[-1].strip()
    new_row = {table.columns[0]: 'Jaar'}

    # Add field called Jaar with the year that was extracted from title, put it at the first row
    for column in table.columns[1:]:
        new_row.update({column: jaar})
    new_row = pd.DataFrame([new_row])
    table = pd.concat([new_row, table], ignore_index=True)

    return table


def processTable1B(table: pd.DataFrame):
    table = table.dropna(how="all")
    i = 0

    # The 'fieldsWithoutValues' are title fields, they do not contain values in the column
    fieldsWithoutValues = ['individueel toepasselijke bezoldigingsmaximum',
                           '(alle bedragen']

    # For every row in the first column,
    table.reset_index(level=0, drop=True, inplace=True)
    while i < len(table.iloc[:, 0]):
        row = table.iloc[i, 0]

        # check if the field isNaN, if it is, make a new row with the data from that row
        if isNaN(row):
            upperNeighbour = table.iloc[i - 1, 0]
            lowerNeighbour = table.iloc[i + 1, 0]
            new_row = {table.columns[0]: str(upperNeighbour) + " " + str(lowerNeighbour)}

            # Fill the new row up with the values that are present in the other columns
            for column in table.columns[1:]:
                new_row.update({column: table[column].iloc[i]})

            # Divide table in upper and lower half so that the new row can be inserted
            upperHalf = table[:][:i - 1]
            lowerHalf = table[:][i + 2:]
            new_row = pd.DataFrame([new_row])
            i -= 1

            table = pd.concat([upperHalf, new_row, lowerHalf], ignore_index=True)
            table.reset_index(level=0, drop=True, inplace=True)

        # check if it is a fieldWithoutValue. If it is, remove that row
        elif any(fieldWithoutValues in str(row).lower() for fieldWithoutValues in fieldsWithoutValues):
            table.drop(index=i, inplace=True)
            i -= 1

        # check if it is this specific field, because that field is stored over three rows, combine into one
        elif "Individueel toepasselijke maximum gehele" in row:
            three_in_one = table.iloc[i:i + 3, 0]
            new_row = {table.columns[0]: " ".join(three_in_one)}
            index = i
            for item in three_in_one:
                for column in table.columns[1:]:
                    if not isNaN(table[column].iloc[index]):
                        new_row.update({column: table[column].iloc[index]})
                index += 1

            new_row = pd.DataFrame([new_row])
            upperHalf = table[:][:i]
            lowerHalf = table[:][i + 3:]

            table = pd.concat([upperHalf, new_row, lowerHalf], ignore_index=True)

        # reset the index  0,1,2,3 etc because some things were removed and switched around
        table.reset_index(level=0, drop=True, inplace=True)

        i += 1

    return table


def processTable1C(table: pd.DataFrame):

    return table


def processTable1D(table: pd.DataFrame):
    # Extract Jaar from title
    jaar = table.columns[0].split(" ")[-1].strip()

    # Create new column called Jaar with the jaar from title
    new_column = []
    for row in table[table.columns[0]]:
        new_column.append(jaar)
    table['Jaar'] = new_column

    # Rename the "Unnamed" and "Gegevens 2020" to "Naam topfunctionaris" and "Functie"
    for columnname in table.columns[:-1]:
        table = table.rename(columns={columnname: table[columnname].iloc[0]})

    # Drop the first row containing "Naam topfunctionaris" and "Functie"
    table.drop(index=0, inplace=True)

    # reset the index  0,1,2,3 etc because some things were removed and switched around
    table.reset_index(level=0, drop=True, inplace=True)

    return table


def processTable1E(table: pd.DataFrame):

    return table


def processTable1F(table: pd.DataFrame):

    return table


def processTable1G(table: pd.DataFrame):

    return table


def processTable2(table: pd.DataFrame):

    return table


def processTable3(table: pd.DataFrame):

    return table



def removeEmptyColumns(table: pd.DataFrame):
    '''
    Removes empty columns if they are there.
    Empty column is defined as a column that has more than 70% of values as nan.
    :param table:
    :type table: pd.DataFrame
    :return: table with empty columns removed
    :rtype: pd.DataFrame
    '''
    for column in table.columns:
        totalEmptyFields = table[column].isna().sum()
        totalFields = table[column].size
        if totalEmptyFields > (math.floor(0.7*totalFields)):
            table = table.drop(columns=column)
    return table


def splitUpperLowerTable(table: pd.DataFrame):
    '''
    Many tables exist of an upper and lower table. Upper table often is the current year, Lower is of last year.
    If there are two tables, this function splits the table into upper and lower and returns them.
    Else, it returns the table as inserted.
    :param table:
    :type table: pd.DataFrame
    :return: table with empty columns removed
    :rtype: pd.DataFrame or List[pd.DataFrame, pd.DataFrame]
    '''
    # split into lower and upper table
    uppertable = pd.DataFrame()
    lowertable = pd.DataFrame()

    isTwoTables = False
    i = 0

    tables = []
    # checks every row, excluding the first four.
    for row in table[table.columns[0]][4:]:
        row = str(row).lower().strip()
        if "gegevens " in row:
            isTwoTables = True
            uppertable = table[:][:i]
            lowertable = table[:][i:]

            lowertable = lowertable.rename(columns={table.columns[0]: row.capitalize()})
            '''
            jaar = row.split(" ")[-1].strip()
            new_row = {lowertable.columns[0]: 'Jaar'}
            for column in lowertable.columns[1:]:
                new_row.update({column: jaar})
            new_row = pd.DataFrame([new_row])
            lowertable = pd.concat([new_row, lowertable], ignore_index=True)
            '''
        i += 1
    if isTwoTables:
        uppertable = removeEmptyColumns(uppertable)
        lowertable = removeEmptyColumns(lowertable)

        uppertable = uppertable.dropna()
        lowertable = lowertable.dropna()

        tables.append(uppertable)
        tables.append(lowertable)
    else:
        tables.append(table)

    return tables


def isNaN(value):
    return value != value

## ALL CODE BELOW IS ONLY RETAINED FOR DOCUMENTATION OF PROCESS, IT HAS NO FUNCTION AND WILL BE DISCARDED IN LATER VERSION
## getTableFromPDF1-8 are failed attempts to get table data from PDF

def getTableFromPDF1():
    '''
    Could not find object
    :return:
    :rtype:
    '''
    import PyPDF2

    pdfObj = open('PDFs/2020/All/0 - ABG-organisatie/1. Wel WNT.pdf', 'rb')

    reader = PyPDF2.PdfFileReader(
        pdfObj,
        strict=True,
        warndest=None,
        overwriteWarnings=True
    )

    print(reader.getNamedDestinations())

    file = "PDFs/2020/All/0 - ABG-organisatie/1. Wel WNT.pdf"
    pdf = PyPDF2.PdfFileReader(file, strict=False).getFields()
    #pdf.getFormTextFields()
    print(pdf)


def getTableFromPDF2():
    from pdfreader import SimplePDFViewer, PageDoesNotExist
    file = "PDFs/2020/All/0 - ABG-organisatie/1. Wel WNT.pdf"

    fd = open(file, "rb")
    viewer = SimplePDFViewer(fd)

    plain_text = ""
    pdf_markdown = ""
    try:
        while True:
            viewer.render()
            pdf_markdown += viewer.canvas.text_content
            plain_text += "".join(viewer.canvas.strings)

            #### put your parsing code here ####

            viewer.next()
    except PageDoesNotExist:
        pass


def getTableFromPDF3():
    import xml.etree.ElementTree as ET
    import requests
    file = "PDFs/2020/All/0 - ABG-organisatie/1. Wel WNT.pdf"

    # Make request to PDFX
    pdfdata = open(file, 'rb').read()
    request = requests.get('http://pdfx.cs.man.ac.uk', pdfdata, headers={'Content-Type': 'application/pdf'})
    response = request.text

    # Parse the response
    tree = ET.fromstring(response)
    for tbox in tree.findall('.//region[@class="DoCO:TableBox"]'):
        src = ET.tostring(tbox.find('content/table'))
        info = ET.tostring(tbox.find('region[@class="TableInfo"]'))
        caption = ET.tostring(tbox.find('caption'))


def getTableFromPDF4():
    # only gets metadata and alltext
    import pdfx
    pdf = pdfx.PDFx("PDFs/2020/All/0 - ABG-organisatie/1. Wel WNT.pdf")
    metadata = pdf.get_metadata()
    text = pdf.get_text()
    references_list = pdf.get_references()
    references_dict = pdf.get_references_as_dict()
    print(text)


def getTableFromPDF5():
    '''
    gets all PDF Elements, can start once element contains title of table
    cant locate ending, has difficulties with columns vs rows
    '''
    from pdfminer.high_level import extract_pages
    import pdfminer.layout as layout
    file = "PDFs/2020/All/0 - ABG-organisatie/1. Wel WNT.pdf"
    extracted_pages = extract_pages(file)
    extracted_pages_list = []
    for page_layout in extracted_pages:
        for element in page_layout:
            if isinstance(element, layout.LTTextContainer):
                elements = element.get_text().split("\n\n")
                if element.get_text().count("\n") > 1:
                    elements = element.get_text().split("\n")

                for elem in elements:
                    extracted_pages_list.append(elem)

    for element in extracted_pages_list:
        if "Bezoldiging topfunctionarissen" in element:
            print(element)
            print(extracted_pages_list.index(element))


def getTableFromPDF6():
    import win32com.shell.shell as shell
    commands = 'pip --version'
    response = shell.ShellExecuteEx(lpVerb='runas', lpFile='cmd.exe', lpParameters='/c ' + commands)
    print(response)


def getTableFromPDF7():
    '''
    Creates error. CalledProcessError
    (retcode, process.args, subprocess.CalledProcessError: Command '['less', 'test.pdf']' returned non-zero exit status 1.
    :return:
    :rtype:
    '''
    import subprocess
    import re
    file = "test.pdf"

    output = subprocess.check_output(["less", file], shell=True)

    re_data_prefix = re.compile("^[0-9]+[.].*$")
    re_data_fields = re.compile("(([^ ]+[ ]?)+)")
    for line in output.splitlines():
        if re_data_prefix.match(line):
            print(l[0].strip()for l in re_data_fields.findall(line))


def getTableFromPDF8():
    '''
    Requires specific type of image before locating a table
    :return:
    :rtype:
    '''
    #pytesseract.pytesseract.tesseract_cmd = r'C:\Users\msi\AppData\Local\Programs\Python\Python38\Lib\site-packages\tesseract'
    import cv2
    image = "test_table.bmp"
    BLUR_KERNEL_SIZE = (17, 17)
    STD_DEV_X_DIRECTION = 0
    STD_DEV_Y_DIRECTION = 0
    blurred = cv2.GaussianBlur(image, BLUR_KERNEL_SIZE, STD_DEV_X_DIRECTION, STD_DEV_Y_DIRECTION)
    MAX_COLOR_VAL = 255
    BLOCK_SIZE = 15
    SUBTRACT_FROM_MEAN = -2

    img_bin = cv2.adaptiveThreshold(
        ~blurred,
        MAX_COLOR_VAL,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        BLOCK_SIZE,
        SUBTRACT_FROM_MEAN,
    )
    vertical = horizontal = img_bin.copy()
    SCALE = 5
    image_width, image_height = horizontal.shape
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(image_width / SCALE), 1))
    horizontally_opened = cv2.morphologyEx(img_bin, cv2.MORPH_OPEN, horizontal_kernel)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(image_height / SCALE)))
    vertically_opened = cv2.morphologyEx(img_bin, cv2.MORPH_OPEN, vertical_kernel)

    horizontally_dilated = cv2.dilate(horizontally_opened, cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)))
    vertically_dilated = cv2.dilate(vertically_opened, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 60)))

    mask = horizontally_dilated + vertically_dilated
    contours, hierarchy = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
    )

    MIN_TABLE_AREA = 1e5
    contours = [c for c in contours if cv2.contourArea(c) > MIN_TABLE_AREA]
    perimeter_lengths = [cv2.arcLength(c, True) for c in contours]
    epsilons = [0.1 * p for p in perimeter_lengths]
    approx_polys = [cv2.approxPolyDP(c, e, True) for c, e in zip(contours, epsilons)]
    bounding_rects = [cv2.boundingRect(a) for a in approx_polys]

    # The link where a lot of this code was borrowed from recommends an
    # additional step to check the number of "joints" inside this bounding rectangle.
    # A table should have a lot of intersections. We might have a rectangular image
    # here though which would only have 4 intersections, 1 at each corner.
    # Leaving that step as a future TODO if it is ever necessary.
    images = [image[y:y + h, x:x + w] for x, y, w, h in bounding_rects]
    return images


if __name__ == '__main__':
    file = "PDFs/2020/Categories first 17-12-2021/Wel WNT/208 - Gemeente Altena/1. Wel WNT.pdf"
    print(PdfDataMiningProcess(file))


