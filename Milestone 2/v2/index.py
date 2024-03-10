from token_utils import TokenUtils

import math
import os
from collections import Counter

from lxml import html
from json import load as jload, dump as jdump


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
 

class Indexer():

    def __init__(self, pages_path, ii_path, logs_path) -> None:
        self.pages_path = pages_path
        self.ii_path = ii_path
        self.logs_path = logs_path

        self.inverted_index = {}
        self.num_unique_words = 0
        self.num_documents = 0

        self.utils = TokenUtils()
    

    def _get_content(self, loc):
        loc = loc.replace('/', '\\')
        path = os.path.join(self.pages_path, loc)
        tree = html.parse(path)
        root = tree.getroot()
        text = str(root.text_content()) if root is not None else None

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
            tokens = self.utils.tokenize(text)
            token_dict = Counter(tokens)

            def _extend_tokens_to_ii(token_dict):
                for token, count in token_dict.items():
                    frequency = count / len(tokens)
                    idx_list = [i for i in range(len(tokens)) if tokens[i] == token]
                    tag_important = self._contains_important_token(root, token)
                    posting = Posting(loc, token, url, frequency, idx_list, tag_important)
                    if token not in self.inverted_index:
                        self.inverted_index[token] = [posting]
                    else:
                        self.inverted_index[token].append(posting)

            _extend_tokens_to_ii(token_dict)
            if i == 100:
                break
            i += 1

    
    def _contains_important_token(self, root, token):
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
        self.num_unique_words = len(self.inverted_index)
        
        return self.inverted_index


    def load_table(self):
        with open(self.ii_path, 'r') as f:
            table = jload(f)
            self.num_unique_words = table['unique_words']
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
            table['unique_words'] = self.num_unique_words
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
            f.write(f'\tNumber of unique words: {self.num_unique_words}\n')
            f.write(f'\tNumber of documents:: {self.num_documents}\n')
            f.write(f'\tIndex file size: {file_size // 1000}KB\n')
            f.write('\n')


    def print_analytics(self):
        file_size = os.path.getsize(self.ii_path)
        print('Index Analytics Table:')
        print(f'\tNumber of unique words: {self.num_unique_words}')
        print(f'\tNumber of documents: {self.num_documents}')
        print(f'\tIndex file size: {file_size // 1000}KB')
        print()