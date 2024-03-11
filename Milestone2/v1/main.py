import os
from index2 import Indexer

if __name__ == "__main__":
    PAGES_PATH = r"..\..\WEBPAGES_RAW"
    II_PATH = r"..\..\table.json"
    LOGS_PATH = r"..\..\logs.txt"
        
    indexer = Indexer(PAGES_PATH, II_PATH, LOGS_PATH)

    if os.path.isfile(II_PATH):
        indexer.load_table()
    else:
        inverted_index = indexer.construct_index()
        indexer.save_table()

    # indexer.print_ii()
    indexer.save_analytics()
    indexer.print_analytics()

    query = input("Enter your query: ")
    while query:
        response = indexer.search(query)
        if response:
            indexer.save_response(query, response)
            indexer.print_response(query, response)
        query = input("\nEnter your query: ")