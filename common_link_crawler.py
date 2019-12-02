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


def get_page_from_node(category_name):
    try:
        if category_name.startswith('Category:'):
            wiki_page = wikipedia.page(category_name[len('Category:'):])
        else:
            wiki_page = wikipedia.page(category_name)
    except Exception:
        raise
    return wiki_page


def get_links_from_page(page_name):
    links = []

    try:
        links = get_page_from_node(page_name).links
    except Exception:
        print("Title or links unavailable")

    return links

def print_main_page_title_and_links(category):
    try:
        print("Main Wiki page: " + str(get_page_from_node(category).title))
        print("External links: " + str(get_page_from_node(category).links))
    except (TypeError, AttributeError):
        print("Title or links unavailable")

def print_categories_of_page(page):
    for cat in page.categories:
        print(cat)



'''
The function identifies the pages that belong to the categories of 
category_graph_source, and checks which ones of the pages have a category
that belongs to category_graph_dest. 

@:param category_crawler_source: category crawler with a category graph
@:param category_crawler_dest: category crawler with a category graph
@:param mode: select whether the search shall be performed only on the main pages of the categories (-m), or on all the pages belonging to the category (-p),
or on all the links in the pages belonging to the category and pointing at pages that have a gategory in the other graph 

@:return pages_categories_map: a dictionary with keys associated to pages, and for each
item includes a list of tuple (cat_source, cat_dest) indicating the source category, i.e., 
the category to which the page belongs or from which the other category was reached, and the cat_dest, i.e., the category
included in category_graph_dest that is an additional category for the identified page.

@:return pages_url_map = map between main page names and URL  
'''
def identify_page_category_map(category_crawler_source, category_crawler_dest):
    pages_categories_map = {}
    pages_url_map = {}

    nodes_dest = nx.DiGraph(category_crawler_dest.get_category_graph()).nodes
    nodes_source = nx.DiGraph(category_crawler_source.get_category_graph()).nodes

    nodes_dest_category_only = [n for n in nodes_dest if n.startswith('Category:')] #get those nodes that are categories

    for node_source in nodes_source:

        if node_source != 'root_node':

            try:
                reference_page = get_page_from_node(node_source)

                page_url = reference_page.url
                page_title = reference_page.title

                ref_page_cats_source = reference_page.categories #get categories from page

                for ref_page_cat in ref_page_cats_source: #check if any of the categories of the page belong to the categories of the other portal
                    if ('Category:' + ref_page_cat) in nodes_dest_category_only:
                        print("page %s has category %s in common with the other portal" % (page_title, ref_page_cat))

                        if page_title not in pages_categories_map.keys():
                            pages_categories_map[page_title] = []

                        pages_categories_map[page_title].append((node_source, ref_page_cat))

                        pages_url_map[page_title] = page_url
            except (PageError, DisambiguationError):
                print("Page for %s not found or ambiguous" % node_source)

    return pages_categories_map, pages_url_map

'''
This function identifies the links in a category graph, including pages, that point to pages that have a category
in the other category graph. Basically, it computes the overlap between the graphs in terms of links. 
The function is the same as identify_page_category_map, the only difference is that an additional recursion 
is included to access the links in each page. 
'''

def identify_link_category_map(category_crawler_source, category_crawler_dest):
    pages_categories_map = {}
    pages_url_map = {}

    nodes_dest = nx.DiGraph(category_crawler_dest.get_category_graph()).nodes
    nodes_source = nx.DiGraph(category_crawler_source.get_category_graph()).nodes

    nodes_dest_category_only = [n for n in nodes_dest if
                                n.startswith('Category:')]  # get those nodes that are categories

    for node_source in nodes_source:

        if node_source != 'root_node':

            page_links = get_links_from_page(node_source)

            for link_page_name in page_links:
                print(link_page_name)

                try:

                    reference_page = get_page_from_node(link_page_name)

                    page_url = reference_page.url
                    page_title = reference_page.title

                    ref_page_cats_source = reference_page.categories  # get categories from page

                    for ref_page_cat in ref_page_cats_source:  # check if any of the categories of the page belong to the categories of the other portal
                        if ('Category:' + ref_page_cat) in nodes_dest_category_only:
                            print("page %s has category %s in common with the other portal" % (page_title, ref_page_cat))

                            if page_title not in pages_categories_map.keys():
                                pages_categories_map[page_title] = []

                            pages_categories_map[page_title].append((link_page_name, ref_page_cat))

                            pages_url_map[page_title] = page_url

                except (PageError, DisambiguationError):
                    print("Page for %s not found or ambiguous" % link_page_name)

    return pages_categories_map, pages_url_map

def get_common_linked_pages(category_crawl_A, category_crawl_B):

    cat_map_A, url_map_A = identify_link_category_map(category_crawl_A, category_crawl_B)
    cat_map_B, url_map_B = identify_link_category_map(category_crawl_B, category_crawl_A)

    common_pages = set(cat_map_A.keys()).union(set(cat_map_B.keys()))
    common_urls = set(url_map_A.values()).union(set(url_map_B.values()))

    return common_pages, common_urls

def get_common_pages(category_crawl_A, category_crawl_B):

    cat_map_A, url_map_A = identify_page_category_map(category_crawl_A, category_crawl_B)
    cat_map_B, url_map_B = identify_page_category_map(category_crawl_B, category_crawl_A)

    common_pages = set(cat_map_A.keys()).union(set(cat_map_B.keys()))
    common_urls = set(url_map_A.values()).union(set(url_map_B.values()))

    return common_pages, common_urls

'''
Possible intersections are:
- (-m) Common categories for main pages: main pages from any of the category graphs that have a category in common with the other graph
- (-p) Common pages: pages form any of the category graphs that have a category in commmon with the other graph
- (-l) Common links: links included in the pages of any category graph and having a category in common with the other graph
'''

def main():
    portal_A = sys.argv[1:][0]
    portal_B = sys.argv[1:][1]
    subcategory_depth = int(sys.argv[1:][2])
    mode = sys.argv[1:][3]


    if mode == '-m': #m: get common main pages
        m_include_pages = False
        out_message = 'Thesa are the main pages from any of the two category graphs that have a category in common with the other graph'
    elif mode == '-p':
        m_include_pages = True
        out_message = 'Thesa are the pages from any of the two category graphs that have a category in common with the other graph'
    elif mode == '-l':
        m_include_pages = True
        out_message = 'Thesa are the links from any of the pages of the two category graphs that have a category in common with the other graph'
    else:
        return -1

    d_A = CategoryCrawler(portal_A)
    d_A.search_and_store_graph(portal_A, cat_page_id='unknown', subcategory_depth=subcategory_depth, max_depth=10,
                               parent_node="root_node", include_pages=m_include_pages, node_type='name')

    d_B = CategoryCrawler(portal_B)
    d_B.search_and_store_graph(portal_B, cat_page_id='unknown', subcategory_depth=subcategory_depth, max_depth=10,
                               parent_node="root_node", include_pages=m_include_pages, node_type='name')


    if mode == '-m' or mode == '-p':
        common_pages, common_url = get_common_pages(d_A, d_B)
    elif mode == '-l':
        common_pages, common_url = get_common_linked_pages(d_A, d_B)
    else:
        return -1

    print(out_message)

    for item in common_url:
        print(item)
    for item in common_pages:
        print(str(item))


#Call this module as, e.g.: python common_link_crawler.py "Category:Emerging technologies" "Category:Artificial intelligence" 1 -m

if __name__ == "__main__":
    main()
