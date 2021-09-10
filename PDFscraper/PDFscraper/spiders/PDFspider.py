import scrapy

class PDFSpider(scrapy.Spider):
    name = "posts"

    start_urls = [
        'https://suleymen-kandrouch-cv.web.app',
        'https://www.coc.nl/over-ons/jaarverslag'
    ]

    def parse(self, response):
        print(str(response))
        for sentence in response.css('a').getall():
            sentenceList = sentence.split(" ")
            for i, elem in enumerate(sentenceList):
                if 'pdf' in elem:
                    messyLink = str(sentenceList[i].replace("\"", ""))
                    hrefLink = messyLink.split(".pdf")[0] + ".pdf"
                    endLink = hrefLink.split("=")[-1]
                    print("end result: " + endLink)

