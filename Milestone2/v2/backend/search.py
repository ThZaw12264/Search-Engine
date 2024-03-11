from token_utils import TokenUtils

import math
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity

class SearchResult():
    
    def __init__(self, loc, url, title, score=1):
        self.loc = loc
        self.url = url
        self.title = title
        self.score = score
        self.postings =  {}

    def insert(self, token, p):
        self.postings[token] = p

    def update_score(self, val):
        self.score *= val


class SearchEngine():

    def __init__(self, indexer, logs_path):
        self.indexer = indexer
        self.logs_path = logs_path
        self.utils = TokenUtils()


    def _get_all_results(self, query):
        query_tokens = self.utils.tokenize(query)
        search_results = {}
        for token in query_tokens:
            if token in self.indexer.inverted_index:
                for posting in self.indexer.inverted_index[token]:
                    if posting.url in search_results:
                        search_results[posting.url].insert(token, posting)
                    else:
                        search_results[posting.url] = SearchResult(posting.loc, posting.url, posting.title)
                        search_results[posting.url].insert(token, posting)
        
        return list(search_results.values())
    

    def search(self, query):
        results = self._get_all_results(query)
        if not results:
            return
        results = self.score_cosine_similarity(query, results)
        results = self.score_tfidf(results)
        results = self.score_proximity(query, results)
        results = self.score_tags(results)

        # Final score sorting
        sorted_results = sorted(results, key=lambda x: -x.score)

        urls = [(sr.url, sr.title, sr.loc, sr.score) for sr in sorted_results]
        numURLS = len(urls)
        return numURLS, urls[:20]
    

    def tfidf_vectorize(self, query, sr):
        query_vector = []
        sr_vector = []
        query_tokens = self.utils.tokenize(query)
        tokens_dict = Counter(query_tokens)
        for token, count in tokens_dict.items():            
            if token not in self.indexer.inverted_index:
                continue

            dft = len(self.indexer.inverted_index[token])
            idf = math.log(self.indexer.num_documents / dft)

            query_tf = count / len(query_tokens)
            query_tfidf = query_tf * idf
            query_vector.append(query_tfidf)
            
            if token in sr.postings:
                sr_tf = sr.postings[token].frequency
                sr_tfidf = sr_tf * idf
                sr_vector.append(sr_tfidf)
            else:
                sr_vector.append(0)

        # print(query_vector, sr_vector)

        return [query_vector], [sr_vector]
    

    def score_cosine_similarity(self, query, results):
        score_list = []

        for result in results:
            query_vector, result_vector = self.tfidf_vectorize(query, result)
            cosine_score = cosine_similarity(query_vector, result_vector)
            score_list.append(cosine_score)
        # print(score_list)
        max_score = max(score_list)
        min_score = min(score_list)

        for idx in range(len(results)):
            score = self.normalize_score(score_list[idx],
                                          minimum=min_score,
                                          maximum=max_score)
            results[idx].update_score(score)
            
        return results
            
        
    def score_tfidf(self, results):
        score_list = []
        
        for result in results:
            tfidf_score = sum([p.tfidf for p in result.postings.values()])
            score_list.append(tfidf_score)

        max_score = max(score_list)
        min_score = min(score_list)

        for idx in range(len(results)):
            score = self.normalize_score(score_list[idx],
                                          minimum=min_score,
                                          maximum=max_score)
            results[idx].update_score(score)
        return results

        
    def score_proximity(self, query, results):

        def calc_adjacency_coeff(adjacent_pairs):
            return (-1 / ((adjacent_pairs + 1) / 4)) + 5
            
        query = self.utils.tokenize(query)
        for result in results:
            adjacent_pairs = 0
            for token_idx in range(1, len(query)):
                t1 = query[token_idx]
                t2 = query[token_idx-1]
                if t1 in result.postings and t2 in result.postings:
                    p1 = result.postings[t1]
                    p2 = result.postings[t2]
                    idx1 = idx2 = 0

                    while idx1 < len(p1.idx_list) and idx2 < len(p2.idx_list):
                        if abs(p1.idx_list[idx1] - p2.idx_list[idx2]) == 1:
                            adjacent_pairs += 1
                            idx1 += 1
                            idx2 += 1
                        elif p1.idx_list[idx1] <  p2.idx_list[idx2]:
                            idx1 += 1
                        else:
                            idx2 += 1
                    
            adj_score = calc_adjacency_coeff(adjacent_pairs)

            adj_score = self.normalize_score(adj_score,
                                             minimum=1,
                                             maximum=5)

            result.update_score(adj_score) 
        
        return results

    

    def score_tags(self, results):
        for result in results:
            tags_score = 1
            for posting in result.postings.values():
                if posting.tag_important:
                    tags_score += 0.5
            result.update_score(tags_score)
        return results
        

    def normalize_score(self, score, minimum, maximum):
        if maximum == minimum:
            return 1
        return 1 + ((score - minimum) / (maximum - minimum))
    
    
    def save_response(self, query, response):
        with open(self.logs_path, 'a') as f:
            num_results, search_results = response
            f.write(f'Query: {query}\n')
            f.write(f'Number of Results: {num_results}\n')
            f.write(f'Top Results (up to 20):\n')
            for i, sr in enumerate(search_results):
                f.write(f'\tRESULT {i+1}: {sr}\n')
            f.write('\n')


    def print_response(self, query, response):
        num_results, search_results = response
        print(f'Query: {query}')
        print(f'Number of Results: {num_results}')
        print(f'Top Results (up to 20):')
        for i, sr in enumerate(search_results):
            print(f'\tRESULT {i+1}: {sr[-1]}, {sr[1]}, {sr[0]}')
        print()
