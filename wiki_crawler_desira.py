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





API_URL = 'http://en.wikipedia.org/w/api.php'


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


class CategoryCrawler(object):

    def __init__(self, main_portal):
        # This graph will include all the explored pages
        self.category_graph = nx.DiGraph()
        self.category_graph.add_node("root_node")
        self.main_cat = main_portal

    #Note that the title of the page can be different from the category,
    #but (in most of the cases), the wikipedia API gets the right page.
    def _get_main_page_from_category(self, category_name):
        try:
            wiki_page = wikipedia.page(category_name.lstrip(u'Category:'))
        except PageError:
            wiki_page = "No main page"
        except DisambiguationError:
            wiki_page = "Main page ambiguous"
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

    def search_and_store_graph(self, category, subcategory_depth=2, max_depth=10, parent_node='root_node', include_pages=False, node_type='url'):
        '''
        This function is called recursively to explore the tree of categories from
        Wikipedia.
        :param category: category name to search
        :param subcategory_depth: depth to explore in the tree of subcategories
        :param parent_node: parent node in the graph
        :param: include_pages: if True adds also the pages to the graph and not only the categories
        (may result in large graphs)
        :return: none
        '''

        #indent based on the depth of the category: visualisation problems may occur if max_depth is not >> subcategory_depth * 2
        category_url = "https://en.wikipedia.org/wiki/" + category.replace(" ", "_")
        print(" " * ((max_depth) - (subcategory_depth * 2)) + category + " URL: " + category_url)

        #adding the category to the graph

        #==========URL as attribute=======
        #category_node = category.replace('Category:', '')
        #category_graph.add_node(category_node, attr_dict= {'url': category_url})
        #=================================

        if node_type == 'url':
            category_node = category_url
        elif node_type == 'name':
            category_node = category
        else:
            print("Node type must be url or name")
            return 0

        self.category_graph.add_edge(parent_node, category_node)
        new_parent_node = category_node
        title = category if category.startswith('Category:') else 'Category:' + category

        try:
            print("Main Wiki page: " + str(self._get_main_page_from_category(category).title))
        except (TypeError, AttributeError):
            print("Title unavailable")

        #=========Adding the pages to the categories, if required (generates a very large graph)====
        # Check this website for param structure: https://www.mediawiki.org/wiki/API:Categorymembers
        if include_pages == True:
            search_params_pages = {
                'list': 'categorymembers',
                'cmtype': 'page',
                'cmlimit': 500,
                'cmtitle': title,
            }

            page_results = _wiki_request(search_params_pages)['query']['categorymembers']
            for page_result in page_results:
                page_url = 'https://en.wikipedia.org/wiki/' + page_result['title'].replace(" ", "_")
                page_title = page_result['title']
                print(" " * ((max_depth) - (subcategory_depth * 2)) + page_result['title'] + " URL: " + page_url)

                if node_type == 'url':
                    page_node = page_url
                elif node_type == 'name':
                    page_node = page_title
                else:
                    print("Node type must be url or name")
                    return 0

                self.category_graph.add_edge(new_parent_node, page_node)

        #=======Adding and exploring the subcategories===
        if subcategory_depth > 0:
            search_params_subcat = {
                'list': 'categorymembers',
                'cmtype': 'subcat',
                'cmlimit': 500,
                'cmtitle': title,
            }
            subcat_results = _wiki_request(search_params_subcat)['query']['categorymembers']

            for subcat_result in subcat_results:
                self.search_and_store_graph(subcat_result['title'], subcategory_depth - 1, max_depth, new_parent_node, include_pages, node_type)

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
    d.search_and_store_graph(portal, subcategory_depth, max_depth=10, parent_node = "root_node")

    graph_file_name = portal + '_D' + str(subcategory_depth) + '_category_graph.gexf'
    nx.write_gexf(d.get_category_graph(), graph_file_name)

if __name__ == "__main__":
    main()


