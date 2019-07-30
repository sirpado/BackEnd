# -*- coding: utf-8 -*-
from Scrapers.AWebScraper import AWebScraper
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import hashlib
import re

PAGE_NUMBER_LIMIT = 6


class NikiBScraper(AWebScraper):

    def number_of_pages_to_search(self,searchURL):
        search_result_page = urlopen(searchURL)
        soup = BeautifulSoup(search_result_page, 'html.parser')
        result = soup.find_all('div', attrs={'id': 'search-filter-results-97174'})
        return int(result[0].contents[10][-2:])


    #Scrape recepies links from search page
    def getLinks(self,number_of_pages, search_result, recipe_links):
        for page in range(1, number_of_pages + 1):
            try:
                searchResultWithPageNumber = search_result + '&sf_paged=' + page.__str__()
                search_result_page = urlopen(searchResultWithPageNumber)
                soup = BeautifulSoup(search_result_page, 'html.parser')
                links = soup.find_all('a',
                                      attrs={'href': re.compile("https://nikib.co.il/.{0,200}/\d{2,6}/"), 'rel': "bookmark"})
                for link in links:
                    encoded_link = str(link.attrs['href']).encode('utf-8')
                    hashed_link = hashlib.sha1(encoded_link)
                    self.lock.acquire()
                    if link.parent.name == 'h3' and hashed_link not in self.visited:
                        recipe_links[link.attrs['href']] = str(link.attrs['title'])
                        self.visited.append(hashed_link)
                    self.lock.release()
            except TimeoutError:
                continue


    def find_ingredients(self,link_dict,queue):
        for link in link_dict:
            try:
                r = requests.get(link)
                soup = BeautifulSoup(r.text, 'html.parser')
                results = soup.find_all('div', attrs={'class': 'ingredients-list t-3of5'})
                ingredients = results[0].find('p')
                if ingredients == None :
                    continue
                words = results[0].text.split("\n")
                filtered_ingredients = words[1:-1]
                filtered_ingredients.remove('מרכיבים:')
                queue.put([link_dict[link],link,filtered_ingredients])
            except TimeoutError:
                continue


    #Override method from abstract class
    def scrape(self,searchWords,queue):
        try:
            search_url = super(NikiBScraper, self).getSearchUrl(searchWords)
            search_url = search_url.replace('%20','-')
            number_of_pages = self.number_of_pages_to_search (search_url)
            if number_of_pages == 0: #no results
                raise ValueError('0 recipes found')
            elif number_of_pages > PAGE_NUMBER_LIMIT: #hard code limit
                number_of_pages = PAGE_NUMBER_LIMIT
        except IndexError:
            return None

        self.getLinks(number_of_pages, search_url, self.recipe_links)
        self.find_ingredients (self.recipe_links,queue)


    def __init__(self,name,url,visited,lock):
        self.url = url
        self.name = name
        self.visited = visited
        self.lock = lock
        self.recipe_links = {}
        self.search_result = {}


###############For DEBUG Use Only#######################################################
# def getInput(self):
#     search_result = 'https://nikib.co.il/search-results/?_sft_ingredients='
#     while True:
#         search_input = input("אנא הקלד פריטים אותם תרצה לחפש לסיום הקלד חפש" + '\n')
#         search_input = search_input.replace('%20','-')
#         if search_input == 'חפש':
#             break
#         if search_result[-1] == '=':
#             search_result = search_result + quote(search_input)
#         else:
#             search_result = search_result + '+' + quote(search_input)
#     return search_result
##########################################################################################
