# -*- coding: utf-8 -*-
from Scrapers.WallaFoodScraper import WallaFoodScraper
from Scrapers.nikibScraper import NikiBScraper
from queue import Queue
import threading
import itertools

walla_food_link = 'https://food.walla.co.il/recipes?page=1&q='
nikiB_link = 'https://nikib.co.il/search-results/?_sft_ingredients='


def rankRecipes(values, search_words, urgent_products):
    recipearray = []
    number_of_matching_ingredients = 0
    number_of_urgent_products = 0

    for recipe in values:
        ingredients = recipe[2]
        for word in ingredients:
            for search_word in search_words:
                if search_word in word:
                    number_of_matching_ingredients = number_of_matching_ingredients + 1
            for urgent_product in urgent_products:
                if urgent_product in word:
                    number_of_urgent_products = number_of_matching_ingredients + 1

        if len(urgent_products) > 0:
            score = float(number_of_matching_ingredients / len(search_words)) + float(number_of_urgent_products * 2 /
                                                                                      len(urgent_products))
        else:
            score = float(number_of_matching_ingredients / len(search_words))

        if score > 10.0:
            score = 10.0
        score = float("{0:.2f}".format(score))
        recipearray.append({"name":recipe[0], "link":recipe[1], "score": score})
    return recipearray


def scrape(search_words, urgent_products):
    queues = []
    threads = []
    values = []
    wallaq = Queue()
    nikibq = Queue()
    visited = []

    queues.append(wallaq)
    queues.append(nikibq)

    lock = threading.Lock()

    walla_scraper = WallaFoodScraper('WallaFood', walla_food_link, visited, lock)
    nikib_scraper = NikiBScraper('NikiB', nikiB_link, visited, lock)

    # split all the search words in to combinations in the length of 3 to get more recipes
    if len(search_words) > 3:
        possible_combinations = itertools.combinations(search_words, 3)
        for combination in possible_combinations:
            search_words = []
            for word in combination:
                search_words.append(word)
            threads.append(threading.Thread(target=walla_scraper.scrape, args=(search_words, nikibq)))
            threads.append(threading.Thread(target=nikib_scraper.scrape, args=(search_words, nikibq)))

    else:
        threads.append(threading.Thread(target=nikib_scraper.scrape, args=(search_words, nikibq)))
        threads.append(threading.Thread(target=walla_scraper.scrape, args=(search_words, wallaq)))

    for thread in threads:
        try:
            thread.start()
            thread.join()

        except ValueError:
            print(ValueError.__str__())
        except:
            print("Error: unable to start thread")

    for queue in queues:
        if queue.qsize() != 0:
            while queue.empty() is False:
                values.append(queue.get())

    ranked_recipes = rankRecipes(values, search_words, urgent_products)
    return  ranked_recipes

#################################for DEBUG use only#########################################
# def getInput():
#     search_words = []
#     while True:
#         search_input = input("אנא הקלד פריטים אותם תרצה לחפש לסיום הקלד חפש" + '\n')
#         if search_input == 'חפש':
#             return search_words
#         else:
#             search_words.append(search_input)
#
# if __name__ == '__main__':
#     queues = []
#     threads = []
#     wallaq = Queue()
#     nikibq = Queue()
#     visited = []
#
#     queues.append(wallaq)
#     queues.append(nikibq)
#
#     searchWords = getInput()
#     lock = threading.Lock()
#
#     wallaScrapper = WallaFoodScraper('WallaFood', walla_food_link,visited,lock)
#     nikibScraper = NikiBScraper('NikiB', nikiB_link,visited,lock)
#     wallaScrapper.scrape(searchWords,wallaq)
#     #split all the search words in to combinations in the length of 3 to get more recipes
#     if (len(searchWords) > 3):
#         possible_combinations = itertools.combinations(searchWords,3)
#         for combination in possible_combinations:
#             searchWords = []
#             for word in combination:
#                 searchWords.append(word)
#
#     scrape(searchWords,[])
#
#     for thread in threads:
#         try:
#             thread.start()
#             thread.join()
#         except:
#             print ("Error: unable to start thread")
#
#     for queue in queues:
#         print (queue.qsize())

