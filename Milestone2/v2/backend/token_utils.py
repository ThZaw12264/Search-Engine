import re
import spacy
import string

class TokenUtils():
    
    def __init__(self):
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


    def _lemmatize(self, tokens):
        lemmatized_tokens = [token.lemma_.lower() for token in tokens]

        return lemmatized_tokens                       


    def _remove_stopwords(self, tokens):
        stopwords = self.nlp.Defaults.stop_words   
        clean_tokens = [word for word in tokens if word not in stopwords]

        return clean_tokens


    def tokenize(self, text):
        tokens = self._load_tokens(text)
        valid_tokens = self._remove_nonwords(tokens)
        lemmatized_tokens = self._lemmatize(valid_tokens)
        clean_tokens = self._remove_stopwords(lemmatized_tokens)

        return clean_tokens