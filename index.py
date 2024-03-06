import math
import os
import re
import string
from collections import Counter

import spacy
from lxml import html
from json import load as jload, dump as jdump

class Posting():
    N = None

    def __init__(self, url, frequency, idx_list, tfidf = 0):
        self.url = url
        self.frequency = frequency
        self.idx_list = idx_list
        self.tfidf = tfidf

    def __repr__(self):
        return f'URL: {self.url}, count: {self.frequency}, tf-idf: {self.tfidf}'

    def set_tfidf(self, tfidf):
        self.tfidf = tfidf

    @staticmethod
    def set_N(N):
        Posting.N = N
 

class Indexer():

    def __init__(self, iipath, logspath) -> None:
        self.iipath = iipath
        self.logspath = logspath
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
        path = os.path.join("WEBPAGES_RAW", loc)
        tree = html.parse(path)
        root = tree.getroot()
        text = str(root.text_content()) if root else None

        return text
    

    def _initialize_ii(self, urls):
        # i = 0
        for loc, url in urls.items():
            print("Processing", loc)
            text = self._get_content(loc)
            if not text:
                continue
            tokens = self._tokenize(text)
            token_dict = Counter(tokens)
            self._extend_token_to_ii(token_dict, tokens, url)
            # if i == 100:
            #     break
            # i += 1


    def _update_ii(self):
        for postings in self.inverted_index.values():
            dft = len(postings)
            idf = math.log(Posting.N / dft)
            for posting in postings:
                tf = 1 + math.log(posting.frequency)
                tfidf = tf * idf
                posting.set_tfidf(tfidf)
    

    def _extend_token_to_ii(self, token_dict, tokens, url):
        for token, count in token_dict.items():
            idx_list = [i for i in range(len(tokens)) if tokens[i] == token]
            posting = Posting(url, count, idx_list)
            if token not in self.inverted_index:
                self.inverted_index[token] = [posting]
            else:
                self.inverted_index[token].append(posting)


    def construct_index(self, bk_path):
        with open(bk_path, 'r') as f:
            urls = jload(f)

        Posting.set_N(len(urls))
        self.num_documents = len(urls)
        self._initialize_ii(urls)
        self._update_ii()
        
        return self.inverted_index
    

    def _find_postings(self, query):
        query_tokens = self._tokenize(query)
        postings = {}
        for token in query_tokens:
            if token in self.inverted_index:
                for p in self.inverted_index[token]:
                    if p.url in postings:
                        adjacent_pairs = 1
                        p2 = postings[p.url]
                        idx1 = idx2 = 0
                        while idx1 < len(p.idx_list) and idx2 < len(p2.idx_list):
                            if abs(p.idx_list[idx1] - p2.idx_list[idx2]) == 1:
                                adjacent_pairs += 1
                                idx1 += 1
                                idx2 += 1
                            elif p.idx_list[idx1] <  p2.idx_list[idx2]:
                                idx1 += 1
                            else:
                                idx2 += 1

                        postings[p.url] = Posting(p.url,
                                                  p2.frequency + p.frequency,
                                                  p2.idx_list + p.idx_list,
                                                  p2.tfidf * p.tfidf * self.calc_adjacency_coeff(adjacent_pairs))
                    else:
                        postings[p.url] = p

        return postings
    
    def calc_adjacency_coeff(self, adjacent_pairs):
        return (-1 / (adjacent_pairs / 4)) + 5

    def search(self, query):
        postings = self._find_postings(query)
        if not postings:
            return
        sorted_postings = sorted(postings.values(), key=lambda x: -x.tfidf)
        urls = [(p.url, p.tfidf) for p in sorted_postings]
        numURLS = len(urls)
        return numURLS, urls[:20]
    

    def load_table(self):
        with open(self.iipath, 'r') as f:
            table = jload(f)
            self.unique_words = set(table['unique_words'])
            self.num_documents = table['num_documents']
            ii = table['inverted_index']
            for index, postings in ii.items():
                self.inverted_index[index] = []
                for posting in postings:
                    self.inverted_index[index].append(Posting(posting['url'],
                                                              posting['frequency'],
                                                              posting['idx_list'],
                                                              posting['tfidf'])
                                                              )


    def save_table(self):
        with open(self.iipath, 'w') as f:
            table = {}
            table['unique_words'] = list(self.unique_words)
            table['num_documents'] = self.num_documents
            table['inverted_index'] = inverted_index
            jdump(table, f, default=lambda o: o.__dict__)


    def print_ii(self):
        for token, postings in sorted(self.inverted_index.items(), key=lambda x: len(x[1])):
            print(f'TOKEN: {token}')
            for posting in postings:
                print(f'POSTING: {posting}')
            print()


    def save_analytics(self):
        file_size = os.path.getsize(self.iipath)
        with open(self.logspath, 'w') as f:
            f.write('Index Analytics Table:\n')
            f.write(f'\tNumber of unique words: {len(self.unique_words)}\n')
            f.write(f'\tNumber of documents:: {self.num_documents}\n')
            f.write(f'\tIndex file size: {file_size // 1000}KB\n')
            f.write('\n')


    def print_analytics(self):
        file_size = os.path.getsize(self.iipath)
        print('Index Analytics Table:')
        print(f'\tNumber of unique words: {len(self.unique_words)}')
        print(f'\tNumber of documents: {self.num_documents}')
        print(f'\tIndex file size: {file_size // 1000}KB')
        print()

    
    def save_response(self, query, response):
        with open(self.logspath, 'a') as f:
            numURLS, urls = response
            f.write(f'Query: {query}\n')
            f.write(f'Number of URLS: {numURLS}\n')
            f.write(f'Top URLS (up to 20):\n')
            for i, url in enumerate(urls):
                f.write(f'\tURL {i+1}: {url}\n')
            f.write('\n')


    def print_response(self, query, response):
        numURLS, urls = response
        print(f'Query: {query}')
        print(f'Number of URLS: {numURLS}')
        print(f'Top URLS (up to 20):')
        for i, url in enumerate(urls):
            print(f'\tURL {i+1}: {url[1]}{url[0]}')
        print()


    def print_unique_tokens(self):
        print(len(self.inverted_index))



if __name__ == "__main__":
    BKPATH = r"WEBPAGES_RAW\bookkeeping.json"
    IIPATH = r"table.json"
    LOGSPATH = r"logs.txt"
        
    indexer = Indexer(IIPATH, LOGSPATH)

    if os.path.isfile(IIPATH):
        indexer.load_table()
    else:
        inverted_index = indexer.construct_index(BKPATH)
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
