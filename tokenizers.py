from collections import defaultdict
import re
import jsonlines
from typing import List
from tqdm import tqdm
import pickle
import os
import random

# compiled regex for splitting text to words and punctuation
identify_words_regex = re.compile(r"\w+|[^\w\s]", re.UNICODE)

def convert_text_to_words(text: str) -> List[str]:
    """
    Utility function to split text to words and punctuation.
    """
    return identify_words_regex.findall(text)


class Tokenizer(object):
    """
    A generic class that tokenizes text using a given vocabulary.
    """

    def __init__(self, vocab_size: int = 1000):
        self.vocab_size = vocab_size # the maximum number of tokens in the vocabulary
        self.token_to_id = {} # map from a token (e.g. 'the') to a unique integer id (e.g. 1)
        self.id_to_token = {} # map from a unique integer id to a token (e.g. 1 -> 'the')

    def tokenize(self, text: str, return_token_ids: bool = False):
        raise Exception("tokenize not implemented")

    def train(self, corpus: List[str]):
        raise Exception("train not implemented")

    def __len__(self):
        raise Exception("__len__ not implemented")


class ReturnWordsTokenizer(Tokenizer):
    def tokenize(self, text: str, return_token_ids: bool = False) -> List[str]:
        return convert_text_to_words(text)
    def train(self, corpus: List[str]):
        pass

class NgramTokenizer(Tokenizer):
    def __init__(self, n: int = 2, vocab_size: int = -1, *args, **kwargs):
        super().__init__(vocab_size, *args, **kwargs)
        self.n = n # n-gram size

    def tokenize(self, text: str, return_token_ids: bool = False) -> List[List[str]] | List[int]:
        """
        Tokenize a text using the NgramTokenizer.
        If return_token_ids is True, return a list of token ids (from 0 to len(vocab)).
        Otherwise, return a list of list of token strings (remember each 'token' is a tuple, e.g. ("hi",) or ("movie", "was")).
        Detailed instructions:
        1. Split the text into words and punctuation using convert_text_to_words utility function.
        2. Iterate over the words, get ngrams of size self.n, and convert them into token ids if return_token_ids is True.
        
        Remember, we ignore ngrams that are not in the vocabulary, and are only looking at ngrams of size self.n.
        
        Example input/outputs:
        self.n = 1
        Input `return_token_ids` = False
        Input `text`: "This movie was really bad, but bad in a fun way, so I loved it."
        Output: [
                ("This",),
                ("movie",),
                ("was",),
                ("really",),
                ("bad",),
                (",",),
                ("but",),
                ("bad",),
                ("in",),
                ("a",),
                ("fun",),
                ("way",),
                (",",),
                ("so",),
                ("I",),
                ("loved",),
                ("it",),
                (".",),
            ],
        return_token_ids = True
        self.n = 3
        Input: "This movie was really bad, but bad in a fun way, so I loved it."
        Output: [16999, 51610, 39000, 44191, 89954, 14539, 50931]
        """

        # 1: Split the text into words and punctuation
        words = convert_text_to_words(text)

        # 2: Extract n-grams of size self.n
        ngrams = [tuple(words[i:i + self.n]) for i in range(len(words) - self.n + 1)]

        if return_token_ids:
            # 3: Convert n-grams to token ids, ignoring those not in the vocabulary
            token_ids = [self.token_to_id[ngram] for ngram in ngrams if ngram in self.token_to_id]
            return token_ids
        
        # 4: Return n-grams as strings, ignoring those not in the vocabulary
        return [ngram for ngram in ngrams if ngram in self.token_to_id]

    def train(self, corpus: List[str]):
        """
        Train the NgramTokenizer on a corpus. Iterate over the corpus, get ngrams, and count their frequencies.
        Detailed instructions:
        1. Initialize the token counts dictionary.
        2. Iterate over the corpus:
            a. Split the text into words and punctuation using convert_text_to_words utility function.
            b. Get ngrams of size self.n, and count their frequencies.
        3. Limit the vocabulary size to the most frequent self.vocab_size words if self.vocab_size is not -1.
        (vocab_size is the maximum number of tokens in the vocabulary, and -1 means no limit)
        
        Example:
        Input `corpus`: ["This movie was good", "This movie was bad"]
        Input `self.n`: 1
        Input `self.vocab_size`: -1
        Output:
        set self.token_to_id: {"This": 0, "movie": 1, "was": 2, "good": 3, "bad": 4}
        set self.id_to_token: {0: "This", 1: "movie", 2: "was", 3: "good", 4: "bad"}
        """
        """
        Train the NgramTokenizer on a corpus.
        - Extracts n-grams and assigns them unique IDs.
        - Limits the vocabulary to `self.vocab_size` most frequent tokens (if applicable).
        """
        token_counts = defaultdict(int)

        # 1. Iterate over the corpus and count n-gram occurrences
        for text in corpus:
            words = convert_text_to_words(text)
            ngrams = [tuple(words[i:i + self.n]) for i in range(len(words) - self.n + 1)]
            
            for ngram in ngrams:
                token_counts[ngram] += 1

        # 2. Sort n-grams by frequency (most common first)
        sorted_ngrams = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)

        # 3. Limit vocabulary if vocab_size is set
        if self.vocab_size != -1:
            sorted_ngrams = sorted_ngrams[:self.vocab_size]

        # 4. Assign unique IDs to n-grams
        self.token_to_id = {ngram: idx for idx, (ngram, _) in enumerate(sorted_ngrams)}
        self.id_to_token = {idx: ngram for ngram, idx in self.token_to_id.items()}

    def __len__(self):
        """
        Return the number of tokens in the vocabulary.
        """
        return len(self.token_to_id)

if __name__ == "__main__":
    with jsonlines.open("data/imdb_train.txt", "r") as reader:
        dataset = list(reader)

    dataset = dataset[:500]

    corpus = [datapoint["text"] for datapoint in dataset]

    unigram = NgramTokenizer(n=1)
    unigram.train(corpus)

    ngram = NgramTokenizer(n=2)
    ngram.train(corpus)

    sample_text = "I love scifi and am willing to put up with a lot. Scifi movies and TV are usually underfunded, under-appreciated and misunderstood."

    print(unigram.tokenize(sample_text))
    print("-" * 100)
    print(ngram.tokenize(sample_text))
    print("-" * 100)
