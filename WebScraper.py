#pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
#pip install googlesearch-python

import time
from googlesearch import search
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from math import floor
import Extra
from lxml import html
from bs4 import BeautifulSoup

def startProcess(year):
    print(storePdfURLs(year))
    #downloadWNTList()


def downloadWNTList():
    # It takes exactly 1 minute to download all the organisation names
    organisationList = []

    # start web browser
    browser = webdriver.Chrome()

    # get source code
    browser.get("https://www.topinkomens.nl/voor-wnt-instellingen/wnt-register")
    html = browser.page_source

    # wait for page to load
    time.sleep(1)

    # get all organisations
    table = browser.find_elements_by_css_selector('tr')
    i = 0
    for line in table:
        # skip first value (title)
        if i > 0:
            name = table[i].find_elements_by_css_selector('td')[0].text.replace("\n", "")
            organisation = clean(name) + "\n"

            organisationList.append(organisation)
        i = i + 1

    # Loop is over, write list to file
    g = open("Extra/WNT-List.txt", "w+")
    for organisation in organisationList:
        g.write(organisation)
        print(organisation)
    g.close()

    # close web browser
    browser.close()


def storePdfURLs(year: int):
    #: This is the main method, it calls searchGoogle() to get links to pdfs
    # and then outputs them to PDF-URLs-List-{year}.txt
    # determine file
    outputFile = "PDF-URLs-List/PDF-URLs-List-%s.txt" % year
    print(outputFile)
    i = 0
    # open inputFile
    with open('Extra/WNT-List.txt') as inputFile:
        inputLines = inputFile.readlines()

        # check if there is already some output so it can continue from there
        with open(outputFile, "r") as output:
            outputLines = output.readlines()
            if len(outputLines) > 0:
                i = int(outputLines[-1].split(":")[0].replace("\n", "")) + 1
            lastOutputLine = i
        print("i = " + str(i))
        # for every line in inputFile it outputs a line in outputFile
        while i < len(inputLines):
            print("___________________________________________________")
            g = open(outputFile, "a")
            foundPDFs = []

            # try except block to catch the report that occurs when we get blocked by google
            try:
                template = "(\"Jaarverslag\"|\"Jaarrekening\"|\"WNT-verantwoording\"|\"Verslaggevingsdocument\"|\"Jaarstuk\") -dnb.com -almanak.overheid.nl filetype:pdf"
                organisation_name = inputLines[i].replace("\n", "")
                foundPDFs = searchGoogle(year, organisation_name, template)
                # proper formatting = [number]: [link1], [link2], [link3] \n
                text = str(i) + ":"
                for PDF in foundPDFs:
                    if foundPDFs.index(PDF) != 0:
                        text = text + ","
                    text = text + " " + PDF
                text = text + "\n"

                # write text to file
                g.write(text)
                g.close()
                print(text)

                # show progress on screen
                print(str(round((i/len(inputLines))*100, 2)) + "% Completed!")
                print("Total lines this session: " + str(i-int(lastOutputLine)))
                i = i+1
                print("Total batches this session: " + str(floor((i-int(lastOutputLine))/116)))

            # if we get blocked by google, wait 2hrs20mins to get unblocked
            except requests.HTTPError:
                print("Too many requests. Waiting 2hrs and 20min for next batch")
                nextBatchTime = datetime.now() + timedelta(hours=2.34)
                print("Next batch scheduled at: " + format(nextBatchTime, '%H:%M:%S'))
                time.sleep(60*60*2.34)
    print(str(round((i / len(inputLines)) * 100, 2)) + "% Completed!")
    return "[---------------------- THE END ------------------------]"


def searchGoogle(year: str, name: str, template: str):

    # prepare searchquery before searching, somehow didnt work if it was directly put into the search() function
    year = "\"" + str(year) + "\""
    name = "\"" + name + "\""
    searchTerm = year + " " + name + " " + template

    # here it actually searches the web
    searchResults = search(searchTerm)

    print("searching for PDF of: " + name)
    print("in year: " + year)

    return searchResults[0:3]


def clean(organisationName):
    # some organisations (#163) had their names double, so here that gets cleaned up.
    # the only risk with this approach is if the organisation organisationName is symmetrical like 'grootoorg'.
    # in that case we should googlesearch both the half and the full organisationName
    # estimated risk chance is < 0.1%
    middleNumber = round(len(organisationName) / 2)

    # determine both halves of the organisation organisationName
    left = organisationName[0:middleNumber]
    right = organisationName[middleNumber:-1] + organisationName[-1]

    # see if both halves are the same, if yes: take the left half
    if left == right:
        organisationName = left

    # Some organisations have a colon in their organisationName
    # Windows doesnt accept this as a valid filename
    # You can either replace it with this "꞉"
    # Or you can replace it with something else entirely like in the code below
    afko = "afgekort: "
    afko2 = "verkorte naam:"
    if afko in organisationName:
        organisationName = organisationName.replace(afko, "(")
        organisationName += ")"
    elif afko2 in organisationName:
        organisationName = organisationName.replace(afko2, "(")
        organisationName += ")"

    # Some organisations also have a slash (/) in their name like number 60: Collectief Alblasserwaard/Vijfheerenlanden Coöperatieve U.A.
    # This breaks the code further down in the mapping system because it sees a slash (/) as a file in a directory
    # A solution to this would be to simply remove the slash or replace it for a unicode that looks like it
    # I chose to replace it for a backward slash (\), didnt work, windows also treats that as a file in a directory
    # Decided to replace backward slash for the word "and", forward slash for the word "en"
    slash = "/"
    slash2 = "\\"
    if slash in organisationName:
        organisationName = organisationName.replace(slash, " en ")
    elif slash2 in organisationName:
        organisationName = organisationName.replace(slash2, " en ")
    return organisationName


def getOrgUrls(year: int):
    outputFile = "Organisations-URLs-List/Organisation-URLs-List-%s-Almanak.txt" % year
    i = 0
    # open inputFile
    with open('Extra/WNT-List.txt', "r") as inputFile:
        inputLines = inputFile.readlines()

        # check if there is already some output so it can continue from there
        with open(outputFile, "w+") as output:
            outputLines = output.readlines()
            if len(outputLines) > 0:
                i = int(outputLines[-1].split(":")[0].replace("\n", "")) + 1
        print("Current iteration = " + str(i))
        # for every organisation it outputs a line in the outputfile containing the URL belonging to that organisation
        allUrls = ''
        while i < len(inputLines):
            print("___________________________________________________")
            g = open(outputFile, "a")

            # try except block to catch the report that occurs when we get blocked by google
            try:
                #searchAlmanak()
                organisation_name = inputLines[i].replace("\n", "")
                organisationURL = searchAlmanak(organisation_name) #drimble allows for up to 300 searches at a time (per day?)

                # proper formatting = [number]: [link1], [link2], [link3] \n

                text = str(i) + ": "
                if organisationURL is not None:
                    text = text + organisationURL
                text = text + "\n"
                print(text)
                allUrls += text
                i += 1

                # if we get blocked by google, wait 2hrs20mins to get unblocked
            except requests.HTTPError:
                print("Too many requests. Waiting 2hrs and 20min for next batch")
                nextBatchTime = datetime.now() + timedelta(hours=2.34)
                print("Next batch scheduled at: " + format(nextBatchTime, '%H:%M:%S'))
                time.sleep(60 * 60 * 2.34)

            # write text to file
            g.write(text)
            g.close()
        print(str(round((i / len(inputLines)) * 100, 2)) + "% Completed!")


def searchAlmanak(organisation_name: str):
    """
        Searches on drimble.nl for the link of the organisation
        drimble.nl contains most companies and some government organisations
        :type organisation_name: str
        :rtype organisatieURL: str
        """

    print('looking for the url of: ' + organisation_name)
    organisation_name = organisation_name.lower() \
        .replace(' ', '%20') \
        .replace('b.v.', 'bv') \
        .replace('b.v', 'bv') \
        .replace('n.v.', 'nv') \
        .replace('n.v', 'nv') \
        .replace('+', '') \
        .replace('Coöperatie', '')
    print(organisation_name)
    url = 'https://www.overheid.nl/zoekresultaat/contactgegevens-overheden/1/10/lijst/field_zoek_organisate[0]=' + organisation_name

    headers = {
        'Host': 'www.overheid.nl',
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6',
        #'Cookie': '_pk_id.7ce2a4e8-d9e0-42ea-a88f-7526a88ab44f.340a=948f660e7ce347d5.1630391910.1.1630391917.1630391910.; _pk_id.074a5050-2272-4f8a-8a07-a14db33f270b.340a=58270e249798fa33.1631090342.1.1631090355.1631090342.; stg_returning_visitor=Fri%2C%2015%20Oct%202021%2007:51:47%20GMT; SSESS6ae35bd3c7413b85293313554b33aca0=Dj843YviV6Ruhx-oeek-r5j1WtFq5fCH1sIh_VfMKHI; SESS6ae35bd3c7413b85293313554b33aca0=eAZfmgzELs1TR2vDRo4bfwnVjY-Jnk9c7i19VkKTTVs; _pk_id.d878bc05-70e8-4720-a8e5-e6bbe995b44e.340a=9e602102d4076a9a.1634284310.9.1636551246.1636551212.; stg_externalReferrer=; _pk_id.1a96e6f9-01b9-4565-8580-046a1491ea57.340a=0afdda59c49e7951.1631083638.18.1636633656.1636633569.; stg_traffic_source_priority=1; _pk_ses.042a8a3e-7692-4e18-8abf-c3034df672d0.340a=*; _pk_ses.3563c399-95ab-4851-b79b-4d4d85b6df10.340a=*; stg_last_interaction=Thu%2C%2011%20Nov%202021%2013:42:43%20GMT; _pk_id.042a8a3e-7692-4e18-8abf-c3034df672d0.340a=07d6d58ddf47a3ba.1634284298.8.1636638164.1636638138.; _pk_id.3563c399-95ab-4851-b79b-4d4d85b6df10.340a=e85c0a43073ae748.1630391910.8.1636638164.1636638138.'
    }
    html = requests.get(url, headers=headers, verify=False).text

    soup = BeautifulSoup(html, 'html.parser')
    almanakURLS = soup.find_all("a", {"class": "result--title"})

    # waar we naar zoeken is <div class="result--list result--list--wide">
    # daarin alle <li><a href=""> </a> </li>
    organisatieURLs = set()
    for url in almanakURLS:
        almanakURL = url['href']

        html = requests.get(almanakURL, verify=False).text
        soup = BeautifulSoup(html, 'html.parser')
        title_elem = soup.find('title').text
        organisatieURL = ""
        if 'Fout: Pagina niet gevonden' not in title_elem:
            #   waar we naar zoeken is
            #   <td data-before="Internet"> <a href="https://www.duoplus.nl">https://www.duoplus.nl</a> </td>
            lijst = str(soup.findAll("td", {"data-before": "Internet"})).split('"')
            if len(lijst) > 3:
                organisatieURL = lijst[3]
            organisatieURLs.add(organisatieURL)
        else:
            print("ERRROOOOOOOOOOOOOORRRRRRRRRRRRR")

    organisatieURLstring = ""

    for i in organisatieURLs:
        organisatieURLstring += ", " + i

    return organisatieURLstring.strip(", ")


def searchDrimble(organisation_name: str):
    """
    Searches on drimble.nl for the link of the organisation
    drimble.nl contains most companies and some government organisations
    :type organisation_name: str
    :rtype organisatieURL: str
    """
    import ssl
    import xml.etree.ElementTree as ET
    ssl._create_default_https_context = ssl._create_unverified_context
    print('looking for the url of: ' + organisation_name)
    organisation_name = organisation_name.lower()\
        .replace(' ', '%20')\
        .replace('b.v.', 'bv')\
        .replace('b.v', 'bv')\
        .replace('n.v.', 'nv')\
        .replace('n.v', 'nv')\
        .replace('+', '')
    print(organisation_name)
    url = 'https://drimble.nl/bedrijfzoek.php?sbi=0&regio=0&input=' + organisation_name

    headers = {
        'Host': 'drimble.nl',
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
        'Accept': '*/*',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://drimble.nl/bedrijf/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6',
        #'Cookie': '_ga=GA1.2.1686978036.1635928626; _pubcid=12efa1b8-0652-438f-8234-fa2d190ef955; euconsent-v2=CPPFuXvPPFuXvDsABANLBzCkAP_AAH_AABpYIUNf_X__bX9j-_59f_t0eY1P9_r3v-QzjhfNt-8F2L_W_L0X42E7NF36pq4KuR4Eu3LBIQNlHMHUTUmwaokVrzHsakWcpyNKJ7LEmnMZO2dYGHtPn9lTuZKY7_78__fz3z-v_t_-39T378X_3_d5_X---_e_V399zLv9____39nN___9v-_8EKACTDUvIAuxLHBk2jSqFECMKwkKgFABRQDC0RWADA4KdlYBHqCFgAhNQEYEQIMQUYMAgAEAgCQiICQAsEAiAIgEAAIAUICEABEwCCwAsDAIABQDQsQIoAhAkIMjgqOUwICJFooJbKwBKCrY0wgDLLACgUf0VGAiUIIFgZCQsHMcASAlwskCAAAA.YAAAAAAAAAAA; DrimbleResp=m1QXGj1nVndyWaxzQ9uGCZ2FKcUNC1t7i%2FILM5a0zC4qTvXsWVIXFhzt2ThtVVRgePimzOqOsKaEtinLOiLb4tsnlYW2hUVsS6uJdI6Z1Z1R59raNmvP0s2TQbykOtcg56RzAA%3D%3D; _gid=GA1.2.461998450.1636552950; _pbjs_userid_consent_data=5935387919608864; __gads=ID=d1388e88a647592e-22538af840cb003c:T=1636552973:RT=1636552973:S=ALNI_MYZohaoGm885HIFcdIv4PuxFo-d_g; WebAdsLayer={"frequencyCap":{"mobileLightBox":1636552976252}}; pbjs-id5id=%7B%22created_at%22%3A%222021-11-10T14%3A02%3A44.390924Z%22%2C%22id5_consent%22%3Atrue%2C%22original_uid%22%3A%22ID5*YU083cHxjZBn7_2wWJgoQBltNNObyIQ5zL2l0lW92MYAACTp5_gpiY8Hfp7s2YAg%22%2C%22universal_uid%22%3A%22ID5*aj9iu7igKoEbkqO4SfArsS1xkX50p5Xks0icYgtrJJIAAJN5P5rANXKVe9V6W127%22%2C%22signature%22%3A%22ID5_AXsGrcLApSWBHX5mEVayyd9OaGge6sCPBZsckzP96caFqv7VIxBob8PnTrEF-_gst6hWTKSd03IfpSNzbzKRe_A%22%2C%22link_type%22%3A2%2C%22cascade_needed%22%3Afalse%2C%22privacy%22%3A%7B%22jurisdiction%22%3A%22gdpr%22%2C%22id5_consent%22%3Atrue%7D%7D; pbjs-id5id_last=Wed%2C%2010%20Nov%202021%2014%3A02%3A56%20GMT; _gat_gtag_UA_15207924_1=1; waNS={"recency":{"DRIMBLE.NL_WEB_BEDRIJF_OUTSTREAM":1635930672277,"DRIMBLE.NL_WEB_BEDRIJF_BILL":1635930717085,"DRIMBLE.NL_WEB_BEDRIJF_RIGHT":1635930717095,"DRIMBLE.NL_WEB_BEDRIJF_LEFT":1635930739619,"DRIMBLE.NL_WEB_LIGHT":1636555831992,"DRIMBLE.NL_WEB_BEDRIJF_APTO":1635930717134,"DRIMBLE.NL_MWEB_BEDRIJF_OUTSTREAM":1635931740573,"DRIMBLE.NL_MWEB_LIGHT":1635931741768,"DRIMBLE.NL_MWEB_BEDRIJF_RM":1635931743541,"DRIMBLE.NL_WEB_112_RIGHT":1636552990476}}'
    }

    requestID = requests.get(url, headers=headers, verify=False)
    try:
        root = ET.fromstring(requestID.text)
    except ET.ParseError:
        return ''

    for i in root.iter('rs'):
        ID = i.attrib.get('deepurl')
        drimbleURL = 'https://drimble.nl/bedrijf/' + ID

        request2 = requests.get(drimbleURL, verify=False)
        print(request2.text)
        if 'Maximum aanvragen van dit soort pagina\'s vandaag bereikt' not in request2.text:
            tree = html.fromstring(request2.text)
            title_elem = tree.cssselect('a')

            for i in title_elem:
                if 'www' in str(i.text):
                    organisatieURL = str(i.text)
                    print(organisatieURL)
                    return organisatieURL

                elif 'http' in str(i.text):
                    organisatieURL = str(i.text)
                    return organisatieURL
        else:
            raise requests.HTTPError


def combineAlmanakDrimble():
    #TODO: Combine Drimble and Almanak url list
    pass


if __name__ == "__main__":
    startProcess(2020)
    #getOrgUrls(2020)

