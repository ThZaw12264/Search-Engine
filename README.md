# Search Engine for UCI ICS Websites

Welcome to our search engine project for ranking websites from the UCI (University of California, Irvine) domain. This project utilizes various ranking algorithms including TF-IDF, cosine similarity, adjacency score, and HTML tag importance to provide accurate search results.

## Overview

This project is divided into two milestones:

1. **Milestone 1: Basic Single Query Token with TF-IDF Ranking**
    - In this milestone, we implement a basic search functionality that supports single-query tokens. The ranking is based solely on TF-IDF (Term Frequency-Inverse Document Frequency) algorithm.

2. **Milestone 2: Multi-Token Query with Enhanced Ranking**
    - In this milestone, we extend the search functionality to support multi-token queries. The ranking system is enhanced with additional algorithms including cosine similarity, adjacency score, and HTML tag importance.

## Contributors

- Husam Solachuddin
- Thar Zaw

## Milestone 1: Basic Single Query Token with TF-IDF Ranking

Description: This milestone focuses on implementing a basic search engine that handles single query tokens and ranks websites based on TF-IDF scores.

### Features Implemented

- Single query token search
- TF-IDF ranking algorithm

## Milestone 2: Multi-Token Query with Enhanced Ranking

Description: In this milestone, we enhance the search engine to support multi-token queries and incorporate additional ranking algorithms for improved search results.

### Features Implemented

- Multi-token query search
- Additional ranking algorithms:
  - [x] Cosine similarity
  - [x] Adjacency score
  - [x] HTML tag importance

## How to Use
#### Console
1. Clone the repository to your local machine.
2. Create a virtual environment and activate it.
3. ```pip install -r requirements.txt```
4. Navigate to the v2 folder in the milestone2 folder.
5. Open the backend folder
6. Run ```python console_main.py```

#### GUI
1. Clone the repository to your local machine.
2. Create a virtual environment and activate it.
3. ```pip install -r requirements.txt```
4. Navigate to the v2 folder in the milestone2 folder.
5. In one terminal, open the backend folder and run: ```uvicorn.exe main:app --reload```
6. In another terminal, open the frontend folder and run these three installs:
   - ```npm install react-scripts```
   - ```npm install react-dom```
   - ```npm install axios```
7. Run ```npm start``` in frontend terminal.
