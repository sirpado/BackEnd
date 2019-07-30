# -*- coding: utf-8 -*-
from Scrapers.WallaFoodScraper import WallaFoodScraper
from Scrapers.nikibScraper import NikiBScraper
from queue import Queue
import threading
import itertools

walla_food_link = 'https://food.walla.co.il/recipes?page=1&q='
nikiB_link = 'https://nikib.co.il/search-results/?_sft_ingredients='

#################################for DEBUG use only#########################################
# def getInput():
#     search_words = []
#     while True:
#         search_input = input("אנא הקלד פריטים אותם תרצה לחפש לסיום הקלד חפש" + '\n')
#         if search_input == 'חפש':
#             return search_words
#         else:
#             search_words.append(search_input)
#############################################################################################

def  rankRecipes(values,searchWords,urgentProducts):
    recipearray = []
    number_of_matching_ingredients = 0
    number_of_urgent_products = 0

    for recipe in values:
        ingredients = recipe[2]
        for word in ingredients:
            for searchWord in searchWords:
                if str(word).__contains__(searchWord):
                    number_of_matching_ingredients = number_of_matching_ingredients + 1
            for urgentProduct in urgentProducts:
                if str(word).__contains__(urgentProduct):
                    number_of_urgent_products = number_of_matching_ingredients + 1
        score = float(number_of_matching_ingredients/len(searchWords))+float(number_of_urgent_products*2/len(urgentProduct))
        if score < 10.0 :
            score = score + number_of_urgent_products
        if score > 10.0:
            score = 10.0

        score = float("{0:.2f}".format(score))
        recipearray.append({"name":recipe[0], "link":recipe[1], "score": score})
    return recipearray


def scrape(searchWords,urgentProducts,cond,recipesQueue):
    queues = []
    threads = []
    values = []
    wallaq = Queue()
    nikibq = Queue()
    visited = []

    queues.append(wallaq)
    queues.append(nikibq)

    lock = threading.Lock()

    wallaScrapper = WallaFoodScraper('WallaFood', walla_food_link, visited, lock)
    nikibScraper = NikiBScraper('NikiB', nikiB_link, visited, lock)

    # split all the search words in to combinations in the length of 3 to get more recipes
    if (len(searchWords) > 3):
        possible_combinations = itertools.combinations(searchWords, 3)
        for combination in possible_combinations:
            searchWords = []
            for word in combination:
                searchWords.append(word)
            threads.append(threading.Thread(target=wallaScrapper.scrape, args=(searchWords, nikibq, cond, recipesQueue)))
            threads.append(threading.Thread(target=nikibScraper.scrape, args=(searchWords, nikibq, cond, recipesQueue)))

    else:
        threads.append(threading.Thread(target=nikibScraper.scrape, args=(searchWords, nikibq, cond, recipesQueue)))
        threads.append(threading.Thread(target=wallaScrapper.scrape, args=(searchWords, wallaq, cond, recipesQueue)))

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

    ranked_recipes = rankRecipes(values,searchWords,urgentProducts)
    return  ranked_recipes


###############################for DEBUG use only##########################################
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
#             threads.append(threading.Thread(target=wallaScrapper.scrape, args=(searchWords, nikibq)))
#             threads.append(threading.Thread(target= nikibScraper.scrape,args=(searchWords,nikibq)))
#
#     else:
#         threads.append(threading.Thread(target= nikibScraper.scrape,args=(searchWords,nikibq)))
#         threads.append(threading.Thread(target = wallaScrapper.scrape, args=(searchWords,wallaq)))
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
##############################################################################################################