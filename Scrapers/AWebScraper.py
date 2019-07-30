from abc import ABC, abstractmethod
from urllib.parse import quote

class AWebScraper(ABC):

    @abstractmethod
    def scrape(self,searchWords,set):
        pass


    #convert the search words's encoding
    def getSearchUrl(self,searchWords):
        search_url = self.url
        if len(searchWords) == 1:
                search_url = search_url + quote(searchWords[0])
        else:
                for word in searchWords:
                    search_url = search_url + '+' + quote(word)
        return search_url