'''
Created on Sept 2019

@author: alessio ferrari
'''
from __future__ import division

import os
import sys

import requests
import wikipedia
from wikipedia.exceptions import PageError, DisambiguationError
import networkx as nx
import re


API_URL = 'http://en.wikipedia.org/w/api.php'
SEARCH_MAIN_ARTICLE_WIN = 1000 #window of chars to search in the content of a category page to identify whether a main article exists
MAIN_ARTICLE_STRING = u'The main article for this <a href="/wiki/Help:Categories" title="Help:Categories">category</a> is <b><a href='
WIKI_PAGE_PREFIX = 'https://en.wikipedia.org/'


def _wiki_request(params):
    '''
    Make a request to the Wikipedia API using the given search parameters.
    Returns a parsed dict of the JSON response.
    '''

    params['format'] = 'json'
    if not 'action' in params:
        params['action'] = 'query'

    r = requests.get(API_URL, params=params)

    return r.json()

def _wiki_search_url_by_ID(page_ID):

    search_page_ID = {
        'prop': 'info',
        'pageids': page_ID,
        'inprop': 'url'
    }

    return _wiki_request(search_page_ID)['query']['pages'][str(page_ID)]['fullurl']

def _wiki_search_cat_ID_by_name(cat_name):
    # Example: https://www.mediawiki.org/w/api.php?action=query&titles=Category:Artificial%20intelligence

    search_cat_ID = {
        'titles': cat_name
    }

    #This searches the first element in the returned json dictionary
    return next(iter(_wiki_request(search_cat_ID)['query']['pages']))

#This funciton search the URL of the main wikipedia page of a certain category
#by inspecting the content of the category page
def _wiki_search_main_page_for_cat(cat_ID):

    params_cat_content = {
        'action': 'parse',
        'pageid': cat_ID,
        'prop': 'text'
    }

    cat_page_initial_content = _wiki_request(params_cat_content)['parse']['text']['*'][:SEARCH_MAIN_ARTICLE_WIN]
    string_index = cat_page_initial_content.find(MAIN_ARTICLE_STRING)
    if not string_index == -1:
        main_page_url_suffix = re.search(r'\"(.+?)\"', cat_page_initial_content[(string_index+len(MAIN_ARTICLE_STRING)):]).group(0)
        main_page_url = WIKI_PAGE_PREFIX + main_page_url_suffix.strip("\"")
        return main_page_url
    else:
        return -1

class CategoryCrawler(object):

    def __init__(self, main_portal):
        # This graph will include all the explored pages
        self.category_graph = nx.DiGraph()
        self.category_graph.add_node("root_node")
        self.main_cat = main_portal


    def _get_main_page_from_category(self, category_name):

    # Note that the title of the page can be different from the category,
    # but (in most of the cases), the wikipedia API gets the right page.
    # in case it doesn't, we raise the error.

        try:
            wiki_page = wikipedia.page(category_name[len('Category:'):])
        except Exception:
            raise
        return  wiki_page

    def get_category_graph(self):
        return self.category_graph

    def write_page_text(self, dir, page):
        file_path = dir + "/" + page['title'].replace('/', '') + '.txt'
        if not os.path.isfile(file_path):
            try:
                txt = wikipedia.page(pageid=page['pageid']).content
                txt_file = open(file_path, "w", encoding="utf-8")
                txt_file.write(txt)
                txt_file.close()
                return True
            except AttributeError:
                print
                'Error on ' + file_path + " " + str(page['pageid'])
            except PageError:
                print
                "Document " + str(page['pageid']) + " Not found!"
            except DisambiguationError:
                print
                "Disambiguation page discarded!"
        return False

    def search_and_store_graph(self, category, cat_page_id='unknown', subcategory_depth=2, max_depth=10, parent_node='root_node', include_pages=False, node_type='url'):
        '''
        This function is called recursively to explore the tree of categories from
        Wikipedia.
        :param category: category name to search
        :param cat_page_id: it is the ID of the category page. If unknown (at the beginning), the page will be searched by name. Otherwise the page is searched by ID.
        :param subcategory_depth: depth to explore in the tree of subcategories
        :param parent_node: parent node in the graph
        :param: include_pages: if True adds also the pages to the graph and not only the categories
        (may result in large graphs)
        :return: none
        '''
        category_url = ("https://en.wikipedia.org/wiki/" + category.replace(" ", "_")) if (cat_page_id == 'unknown') else _wiki_search_url_by_ID(cat_page_id)

        # indent based on the depth of the category: visualisation problems may occur if max_depth is not >> subcategory_depth * 2
        print(" " * ((max_depth) - (subcategory_depth * 2)) + category + " URL: " + category_url)

        #adding the category to the graph
        category_node = category_url if node_type == 'url' else category

        self.category_graph.add_node(category_node, attr_dict={'url': category_url, 'title': category, 'id': cat_page_id})
        self.category_graph.add_edge(parent_node, category_node)

        new_parent_node = category_node

        title = category if category.startswith('Category:') else 'Category:' + category

        try:
            print("Main Wiki page: " + str(self._get_main_page_from_category(category).url))
        except Exception as e:
            print(e)

        #=========Adding the pages to the categories, if required (generates a very large graph)====
        # Check this website for param structure: https://www.mediawiki.org/wiki/API:Categorymembers

        if include_pages == True:
            search_params_pages = {
                'list': 'categorymembers',
                'cmtype': 'page',
                'cmprop': 'ids|title',
                'cmlimit': 500}

            if (cat_page_id=='unknown'):
                search_params_pages['cmtitle'] = title
            else:
                search_params_pages['cmpageid'] = cat_page_id

            page_results = _wiki_request(search_params_pages)['query']['categorymembers']

            for page_result in page_results:

                page_id = page_result['pageid']
                page_url = _wiki_search_url_by_ID(page_id)

                page_title = page_result['title']
                print(" " * ((max_depth) - (subcategory_depth * 2)) + page_title + " URL: " + page_url)

                page_node = page_url if node_type == 'url' else page_title

                self.category_graph.add_node(page_node, attr_dict={'url': page_url, 'title': page_title, 'id': page_id})
                self.category_graph.add_edge(new_parent_node, page_node)

        #=======Adding and exploring the subcategories===
        if subcategory_depth > 0:

            search_params_subcat = {
                'list': 'categorymembers',
                'cmtype': 'subcat',
                'cmprop': 'ids|title',
                'cmlimit': 500}

            if (cat_page_id=='unknown'):
                search_params_subcat['cmtitle'] = title
            else:
                search_params_subcat['cmpageid'] = cat_page_id

            subcat_results = _wiki_request(search_params_subcat)['query']['categorymembers']

            for subcat_result in subcat_results:
                self.search_and_store_graph(subcat_result['title'], subcat_result['pageid'], subcategory_depth - 1, max_depth, new_parent_node, include_pages, node_type)

# To visualise the graph and have the links you should:
# 1. Open the file .gexf with Gephi;
# 2. Export with the plugin Sigma js (Export as: Sigma js template). This generates a folder named "network"
# 3. Open a web server with python3 -m http.server in the folder named "network"
# 4. Open a browser and set localhost:8000. This will visualise the graph

#Call e.g.: python wiki_crawler_desira.py "Category:Artificial intelligence" 2

def main():
    portal = sys.argv[1:][0]
    subcategory_depth = int(sys.argv[1:][1])

    d = CategoryCrawler(portal)
    d.search_and_store_graph(portal, cat_page_id='unknown', subcategory_depth = subcategory_depth, max_depth=10, parent_node = "root_node", include_pages=False, node_type='url')

    graph_file_name = portal + '_D' + str(subcategory_depth) + '_category_graph.gexf'
    nx.write_gexf(d.get_category_graph(), graph_file_name)
    print('Gephi graph saved in ' + graph_file_name)



if __name__ == "__main__":
    main()


