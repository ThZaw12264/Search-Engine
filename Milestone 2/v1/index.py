import math
import os
import re
import string
from collections import Counter

import spacy
from lxml import html
from json import load as jload, dump as jdump
from sklearn.metrics.pairwise import cosine_similarity


class Posting():

    def __init__(self, loc, token, url, frequency, idx_list, tag_important=False, tfidf = 0):
        self.loc = loc
        self.token = token
        self.url = url
        self.frequency = frequency
        self.idx_list = idx_list
        self.tag_important = tag_important
        self.tfidf = tfidf

    def __repr__(self):
        return f'URL: {self.url}, count: {self.frequency}, tf-idf: {self.tfidf}'

    def set_tfidf(self, tfidf):
        self.tfidf = tfidf
        

class SearchResult():
    
    def __init__(self, loc, url, score=1):
        self.loc = loc
        self.url = url
        self.score = score
        self.postings =  {}

    def insert(self, token, p):
        self.postings[token] = p

    def update_score(self, val):
        self.score *= val
 

class Indexer():

    def __init__(self, pages_path, ii_path, logs_path) -> None:
        self.pages_path = pages_path
        self.ii_path = ii_path
        self.logs_path = logs_path
        self.inverted_index = {}
        self.unique_words = set()
        self.num_documents = 0
        self.nlp = spacy.load('en_core_web_sm')


    def _load_tokens(self, text):
        self.nlp.max_length = len(text)
        tokens = self.nlp(text)

        return tokens
    

    def _is_only_spaces(self, token):
        return all(char == ' ' for char in token)


    def _remove_nonwords(self, tokens):
        punc_list = set(list(string.punctuation) + [' '])
        valid_tokens = [token for token in tokens if token.text not in punc_list
                        and not re.search(r'[\r\n\t]', token.text)
                        and not self._is_only_spaces(token.text)]

        return valid_tokens
    

    def _update_unique_words(self, tokens):
        self.unique_words.update([token.lower_ for token in tokens])


    def _lemmatize(self, tokens):
        lemmatized_tokens = [token.lemma_.lower() for token in tokens]

        return lemmatized_tokens                       


    def _remove_stopwords(self, tokens):
        stopwords = self.nlp.Defaults.stop_words   
        clean_tokens = [word for word in tokens if word not in stopwords]

        return clean_tokens


    def _tokenize(self, text):
        tokens = self._load_tokens(text)
        valid_tokens = self._remove_nonwords(tokens)
        self._update_unique_words(valid_tokens)
        lemmatized_tokens = self._lemmatize(valid_tokens)
        clean_tokens = self._remove_stopwords(lemmatized_tokens)

        return clean_tokens
    

    def _get_content(self, loc):
        loc = loc.replace('/', '\\')
        path = os.path.join(self.pages_path, loc)
        tree = html.parse(path)
        root = tree.getroot()
        text = str(root.text_content()) if root else None

        return text, root
    

    def _initialize_ii(self, urls):
        i = 0
        for loc, url in urls.items():
            if '#' in url:
                continue
            print("Processing", loc)
            text, root = self._get_content(loc)
            if not text:
                continue
            tokens = self._tokenize(text)
            token_dict = Counter(tokens)

            def _extend_tokens_to_ii(token_dict):
                for token, count in token_dict.items():
                    frequency = count / len(tokens)
                    idx_list = [i for i in range(len(tokens)) if tokens[i] == token]
                    tag_important = self.contains_important_token(root, token)
                    posting = Posting(loc, token, url, frequency, idx_list, tag_important)
                    if token not in self.inverted_index:
                        self.inverted_index[token] = [posting]
                    else:
                        self.inverted_index[token].append(posting)

            _extend_tokens_to_ii(token_dict)
            if i == 100:
                break
            i += 1

    
    def contains_important_token(self, root, token):
        tags = ['title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b']
        upper_alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lower_alpha = "abcdefghijklmnopqrstuvwxyz"
        xpath_query = " | ".join([f".//{tag}[contains(translate(text(), '{upper_alpha}', '{lower_alpha}'), translate('{token}', '{upper_alpha}', '{lower_alpha}'))]" for tag in tags])
        try:
            elements = root.xpath(xpath_query)
            return len(elements) > 0
        except:
            return False


    def _update_ii(self):
        for postings in self.inverted_index.values():
            dft = len(postings)
            idf = math.log(self.num_documents/ dft)
            for posting in postings:
                tf = posting.frequency
                tfidf = tf * idf
                posting.set_tfidf(tfidf)


    def construct_index(self):
        bk_path = os.path.join(self.pages_path, 'bookkeeping.json')
        with open(bk_path, 'r') as f:
            urls = jload(f)

        self.num_documents = len(urls)
        self._initialize_ii(urls)
        self._update_ii()
        
        return self.inverted_index

    
    def _get_all_results(self, query):
        query_tokens = self._tokenize(query)
        search_results = {}
        for token in query_tokens:
            if token in self.inverted_index:
                for posting in self.inverted_index[token]:
                    if posting.url in search_results:
                        search_results[posting.url].insert(token, posting)
                    else:
                        search_results[posting.url] = SearchResult(posting.loc, posting.url)
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

        urls = [(sr.url, sr.loc, sr.score) for sr in sorted_results]
        numURLS = len(urls)
        return numURLS, urls[:20]
    

    def tfidf_vectorize(self, query, sr):
        query_vector = []
        sr_vector = []
        query_tokens = self._tokenize(query)
        tokens_dict = Counter(query_tokens)
        for token, count in tokens_dict.items():            
            if token not in self.inverted_index:
                continue

            dft = len(self.inverted_index[token])
            idf = math.log(self.num_documents / dft)

            query_tf = count / len(query_tokens)
            query_tfidf = query_tf * idf
            query_vector.append(query_tfidf)
            
            if token in sr.postings:
                sr_tf = sr.postings[token].frequency
                sr_tfidf = sr_tf * idf
                sr_vector.append(sr_tfidf)
            else:
                sr_vector.append(0)

        print(query_vector, sr_vector)

        return [query_vector], [sr_vector]
    

    def score_cosine_similarity(self, query, results):
        score_list = []

        for result in results:
            query_vector, result_vector = self.tfidf_vectorize(query, result)
            cosine_score = cosine_similarity(query_vector, result_vector)
            score_list.append(cosine_score)
        print(score_list)
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
            
        query = self._tokenize(query)
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


    def load_table(self):
        with open(self.ii_path, 'r') as f:
            table = jload(f)
            self.unique_words = set(table['unique_words'])
            self.num_documents = table['num_documents']
            ii = table['inverted_index']
            for index, postings in ii.items():
                self.inverted_index[index] = []
                for posting in postings:
                    self.inverted_index[index].append(Posting(posting['loc'],
                                                              posting['token'],
                                                              posting['url'],
                                                              posting['frequency'],
                                                              posting['idx_list'],
                                                              posting['tag_important'],
                                                              posting['tfidf'])
                                                              )


    def save_table(self):
        with open(self.ii_path, 'w') as f:
            table = {}
            table['unique_words'] = list(self.unique_words)
            table['num_documents'] = self.num_documents
            table['inverted_index'] = self.inverted_index
            jdump(table, f, default=lambda o: o.__dict__)


    def print_ii(self):
        for token, postings in sorted(self.inverted_index.items(), key=lambda x: len(x[1])):
            print(f'TOKEN: {token}')
            for posting in postings:
                print(f'POSTING: {posting}')
            print()


    def save_analytics(self):
        file_size = os.path.getsize(self.ii_path)
        with open(self.logs_path, 'w') as f:
            f.write('Index Analytics Table:\n')
            f.write(f'\tNumber of unique words: {len(self.unique_words)}\n')
            f.write(f'\tNumber of documents:: {self.num_documents}\n')
            f.write(f'\tIndex file size: {file_size // 1000}KB\n')
            f.write('\n')


    def print_analytics(self):
        file_size = os.path.getsize(self.ii_path)
        print('Index Analytics Table:')
        print(f'\tNumber of unique words: {len(self.unique_words)}')
        print(f'\tNumber of documents: {self.num_documents}')
        print(f'\tIndex file size: {file_size // 1000}KB')
        print()

    
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
            print(f'\tRESULT {i+1}: {sr}')
        print()
