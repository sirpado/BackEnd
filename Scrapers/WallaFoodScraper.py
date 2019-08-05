# -*- coding: utf-8 -*-
from urllib.request import urlopen
from Scrapers.AWebScraper import AWebScraper
from bs4 import BeautifulSoup
import requests
import hashlib
import re

PAGE_NUMBER_LIMIT = 6


class WallaFoodScraper(AWebScraper):

    #Scrape recepies links from search page
    def getLinks(self,search_result, recipe_links,counter):
        try:
            url_beginning = 'http://food.walla.co.il'
            search_result_page = urlopen(search_result)
            soup = BeautifulSoup(search_result_page, 'html.parser')
            results = soup.find_all('a',
                                attrs={'href': re.compile("recipe/[0-9]*"), 'class': 'event'})
            for result in results:
                encoded_link = result.text.encode('utf-8')
                hashed_link = hashlib.sha1(encoded_link)
                self.lock.acquire()
                if len(result.parent.parent.attrs['class']) > 1 and hashed_link not in self.visited:
                    recipe_links[url_beginning + result.attrs['href']] = result.text
                    self.visited.append(hashed_link)
                self.lock.release()
        except Exception:
            pass

        #No results
        if len(recipe_links) == 0:
            raise ValueError('0 recipes found')

        #More then one page
        if len(soup.find_all('a', attrs = {'rel': 'next'}) ) > 0 and counter < PAGE_NUMBER_LIMIT:
            next = soup.find_all('a', attrs = {'rel': 'next'})[0]['href']
            self.getLinks(next,recipe_links,counter + 1)

    def find_ingredients(self,link_dict,queue):
        for link in link_dict:
            result_array = []
            try:
                r = requests.get(link)
                soup = BeautifulSoup(r.text, 'html.parser')
                results = soup.find_all('li', attrs={'itemprop': 'recipeIngredient'})
                for result in results:
                    result_array.append(result.text)
                queue.put([link_dict[link],link,result_array])
            except TimeoutError:
                continue

    # Override method from abstract class
    def scrape(self,searchWords,queue):
        search_url = super(WallaFoodScraper,self).getSearchUrl(searchWords)
        try:
            self.getLinks(search_url, self.recipe_links,0)
            self.find_ingredients(self.recipe_links,queue)
        except ValueError as error:
            print(error.args)
            return None

    def __init__(self,name,url,visited,lock):
        self.url = url
        self.name = name
        self.visited = visited
        self.lock = lock
        self.recipe_links = {}
        self.search_result = {}
