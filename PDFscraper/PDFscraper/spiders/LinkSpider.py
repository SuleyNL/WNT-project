import scrapy
from selenium import webdriver
import time

class LinkSpider(scrapy.Spider):
    name = "posts1"

    start_urls = [
        'https://suleymen-kandrouch-cv.web.app',
        'https://www.coc.nl/over-ons/jaarverslag'
    ]

    def parse(self, response):
        linksList = []
        HTMLsentenceList = response.css("a::attr(href)").extract()
        for i, item in enumerate(HTMLsentenceList):
            if 'http' in item:
                foundLink = HTMLsentenceList[i].strip("//")
                linksList.append(foundLink)
        print("Lengte van lijst: " + str(len(linksList)))

        with open("scanned_links.txt") as output:
            outputLines = output.readlines()

        if item not in outputLines:
            print("hoo deze is nieuw hoor: " + item)
            nextPage = item
            print("______________________________NEXT PAGE _________________________________")
            g = open("scanned_links.txt", "a")
            g.write(str(nextPage) + "\n")
            g.close()
            time.sleep(1)
            yield response.follow(nextPage, callback=self.parse)
        if item in outputLines:
            print("deze heb ik al gehad: " + item)
