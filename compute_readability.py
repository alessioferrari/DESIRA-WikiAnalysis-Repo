import wikipedia
import textstat
import requests

API_URL = 'http://en.wikipedia.org/w/api.php'

def _wiki_request_fun(params):
    '''
    Make a request to the Wikipedia API using the given search parameters.
    Returns a parsed dict of the JSON response.
    '''

    params['format'] = 'json'
    if not 'action' in params:
        params['action'] = 'query'

    r = requests.get(API_URL, params=params)

    return r.json()

def get_cat_info(category):
    title = category if category.startswith('Category:') else 'Category:' + category

    search_params = {
            "titles": title,
            "prop": "iwlinks"
            }
    #results = _wiki_request_fun(search_params)['query']['pages']
    results = _wiki_request_fun(search_params)['query']
    print(results)



def print_readability(text_to_analyse, option = 'short'):
    if option == 'all':
        print("flesch (0-29: confusing, 30-59: Difficult, 60-69: Standard, 70-100: Easy): ", textstat.flesch_reading_ease(text_to_analyse))
        print("smog (years of education required): " , textstat.smog_index(text_to_analyse))
        print("flesch kinkaid (70-100: Fairly Easy; 60-70: Plain English; 30-60: Fairly Difficult; 30-0: Very Difficult): ", textstat.flesch_kincaid_grade(text_to_analyse))
        print("coleman liau: ", textstat.coleman_liau_index(text_to_analyse))
        print("auto read (1-4: 5-10 years age; 5-8: 10-14 y; 9-12: 14-18 y; 13-14: 18+): ", textstat.automated_readability_index(text_to_analyse))
        print("dale chall (< 5: kid; 5-8: scholar; 9-10: college): ", textstat.dale_chall_readability_score(text_to_analyse))
        print("difficult words: ", textstat.difficult_words(text_to_analyse))
        print("linsear write: ", textstat.linsear_write_formula(text_to_analyse))
        print("gunning fog (9-12: High-school; 13-17: College): ", textstat.gunning_fog(text_to_analyse))

    print("text standard (estimated school grade level): ", textstat.text_standard(text_to_analyse))

#The function removes all the extra content from wiki pages, so that they can be evaluated for
#readability without considering titles of sections, which normally start with "=".

def clean_wiki_content(in_wiki_page):
    return ("\n".join([l for l in in_wiki_page.splitlines() if (l and not l.startswith("="))]))

page_name = "Artificial Intelligence"

page_content = wikipedia.page(page_name).content
page_summary = wikipedia.page(page_name).summary

print(len(page_content.splitlines()))
print(page_content)

print("Page content readability scores: ")
print_readability(page_content)

print("Clean page content readability scores: ")
print_readability(clean_wiki_content(page_content))

print("\nPage summary readability scores: ")
print_readability(page_summary)

#get_cat_info("Mathematics")

