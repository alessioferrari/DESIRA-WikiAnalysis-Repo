#1. Given two portals, take all the main pages of the categories belonging to one portal, and
#check which ones have links with main pages of the categories of the other portal.

#2. Given the common pages above, consider their category, and return the categories
# related to that one.
import sys

import wikipedia
from wikipedia.exceptions import PageError, DisambiguationError
import networkx as nx

#Given a wikipedia portal name, it returns the main pages associated to the categories of the portal.
from wiki_crawler_desira import CategoryCrawler


#FIXME: check for the actual main page (Computer vision does not work)
#FIXME: some pages are not found, the page ids should be used
def get_main_page_from_category(category_name):
    try:
        wiki_page = wikipedia.page(category_name.lstrip(u'Category:'))
    except (PageError, DisambiguationError):
        raise
    return wiki_page

def get_links_from_main_category_page(category):
    links = []

    try:
        links = get_main_page_from_category(category).links
    except (TypeError, AttributeError):
        print("Title or links unavailable")

    return links

def print_main_page_title_and_links(category):
    try:
        print("Main Wiki page: " + str(get_main_page_from_category(category).title))
        print("External links: " + str(get_main_page_from_category(category).links))
    except (TypeError, AttributeError):
        print("Title or links unavailable")

def print_categories_of_page(page):
    for cat in page.categories:
        print(cat)

'''
The function identifies the main pages that belong to the categories of 
category_graph_source, and checks which ones of the pages have a category
that belongs to category_graph_dest. 

@:param category_crawler_source: category crawler with a category graph
@:param category_crawler_dest: category crawler with a category graph

@:return pages_categories_map: a dictionary with keys associated to pages, and for each
item includes a list of tuple (cat_source, cat_dest) indicating the source category, i.e., 
the category for which the page is a main page, and the cat_dest, i.e., the category
included in category_graph_dest that is an additional category for the identified page.

@:return pages_url_map = map between main page names and URL  
'''
def identify_page_category_map(category_crawler_source, category_crawler_dest):
    pages_categories_map = {}
    pages_url_map = {}

    categories_dest = nx.DiGraph(category_crawler_dest.get_category_graph()).nodes
    categories_source = nx.DiGraph(category_crawler_source.get_category_graph()).nodes

    for cat_source in categories_source:

        if cat_source != 'root_node':

            #if(type(get_main_page_from_category(cat_source)) != str): #If the main page actually exists
            try:
                main_page = get_main_page_from_category(cat_source)
                page_url = main_page.url
                page_title = main_page.title

                #pages_categories_map[page_title] = [] #list of tuples, which will include source_cat and dest_cat

                main_page_cats_source = main_page.categories #get categories from main page

                # print('page url: ' +  page_url)
                # print('categories: ' + str(main_page_cats_source))

                for main_page_cat in main_page_cats_source: #check if any of the categories of the page belong to the categories of the other portal
                    if ('Category:' + main_page_cat) in categories_dest:
                        print("page %s (main page of category %s) has category %s in common with the other portal" % (page_title, cat_source, main_page_cat))

                        if page_title not in pages_categories_map.keys():
                            pages_categories_map[page_title] = []

                        pages_categories_map[page_title].append((cat_source, main_page_cat))

                        pages_url_map[page_title] = page_url
            except (PageError, DisambiguationError):
                print("main page for %s not found or ambiguous" % cat_source)

    return pages_categories_map, pages_url_map


def get_common_main_pages(category_crawl_A, category_crawl_B):

    cat_map_A, url_map_A = identify_page_category_map(category_crawl_A, category_crawl_B)
    cat_map_B, url_map_B = identify_page_category_map(category_crawl_B, category_crawl_A)

    common_main_pages = set(cat_map_A.keys()).union(set(cat_map_B.keys()))
    common_urls = set(url_map_A.values()).union(set(url_map_B.values()))

    return common_main_pages, common_urls

#linked_pages = get_links_from_main_category_page("Category:Artificial intelligence")
#print_categories_of_page(get_main_page_from_category("Category:Artificial intelligence"))

def main():
    portal_A = sys.argv[1:][0]
    portal_B = sys.argv[1:][1]
    subcategory_depth = int(sys.argv[1:][2])

    d_A = CategoryCrawler(portal_A)
    d_A.search_and_store_graph(portal_A, subcategory_depth, max_depth=10, parent_node="root_node", include_pages=True, node_type='name')

    d_B = CategoryCrawler(portal_B)
    d_B.search_and_store_graph(portal_B, subcategory_depth, max_depth=10, parent_node="root_node", include_pages=True, node_type='name')

    common_pages, common_url = get_common_main_pages(d_A,d_B)

    print('Thesa are the main pages from any of the two category graphs that have a category in common with the other graph')
    for item in common_url:
        print(item)

    for item in common_pages:
        print(str(item))


    #identify_page_category_map(d_A, d_B)
    #identify_page_category_map(d_B, d_A)

    # for cat_A in nx.DiGraph(d_A.get_category_graph()).nodes:
    #
    #     if cat_A != 'root_node':
    #
    #         page_title = get_main_page_from_category(cat_A).title
    #
    #         if(type(get_main_page_from_category(cat_A)) != str): #If the main page actually exists
    #
    #             main_page_cats_A = get_main_page_from_category(cat_A).categories #get categories from main page
    #
    #             categories_B = nx.DiGraph(d_B.get_category_graph()).nodes
    #
    #             for main_page_cat in main_page_cats_A: #check if any of the categories of the page belong to the categories of the other portal
    #                 if ('Category:' + main_page_cat) in categories_B:
    #                     print("page %s (main page of category %s) has category %s in common with B" % (page_title, cat_A, main_page_cat))
    #         else:
    #             print("main page for %s does not exist" % cat_A)


#Call this module as, e.g.: python common_link_crawler.py "Category:Emerging technologies" "Category:Artificial intelligence" 1

if __name__ == "__main__":
    main()
