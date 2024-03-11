from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from search import SearchEngine
from index import Indexer
import json
import os

app = FastAPI()
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Include OPTIONS method
    allow_headers=["*"],
)

PAGES_PATH = r"..\..\..\WEBPAGES_RAW"
II_PATH = r"..\..\table.json"
LOGS_PATH = r"..\..\logs.txt"

# Initialize the search engine
indexer = Indexer(PAGES_PATH, II_PATH, LOGS_PATH)
if os.path.isfile(II_PATH):
        indexer.load_table()
else:
    inverted_index = indexer.construct_index()
    indexer.save_table()
            
search_engine = SearchEngine(indexer, LOGS_PATH)

class QueryRequest(BaseModel):
    query: str

@app.post("/search")
def search(query_request: QueryRequest):
    query = query_request.query
    response = search_engine.search(query)
    if response:
        numUrls, searchResults = response
    else:
        return None
    searchResults = [(title, url) for url, title, _, _ in searchResults]
    # searches = {f"Search {i+1}: ": (searchResults[i][0], searchResults[i][1]) for i in range(numUrls)}
    return searchResults
    

@app.options("/search")
def options_search(response: Response):
    response.headers["Allow"] = "POST, OPTIONS"
    return response