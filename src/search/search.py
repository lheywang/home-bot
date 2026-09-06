# ----------------------------------------------------------------------------------
# brief : Define the search class
# author : l.heywang
# date : 06/09/2026
# ----------------------------------------------------------------------------------

# Import
from unidecode import unidecode
from dataclasses import dataclass
import math


@dataclass
class ArticleEntry:
    hash: str
    score: int
    ts: int


class searchEngine:
    """
    Provide the search features from the provided dict.
    Ensure a fast response in any cases.
    """

    def __init__(self):
        """
        Initialize the SearchEngine object.
        """
        self._valid = False
        self.db_ts = 0
        self.db_version = -1
        self.keywords = dict()
        self._articles_by_id = dict()

    # ------------------------------------------
    # DATA HANDLING
    # ------------------------------------------

    def update(self, indata: dict):
        """
        Update the internal database of elements and tokens
        """

        # Fetch raw elements :
        self.db_ts = indata.get("timestamp", 0)
        self.db_version = indata.get("version", 0)
        data = indata.get("data", [])

        # Clear the previous entries
        self.keywords.clear()

        # Iterate over all the tokens articles presents :
        for article in data:

            hash = article.get("hash", "")
            ts = article.get("date", 0)
            tokens = article.get("tokens", {})

            # Add the article to our entry
            for token, value in tokens.items():

                obj = ArticleEntry(hash, value, ts)

                if not token in self.keywords:
                    self.keywords[token] = [obj]
                else:
                    self.keywords[token].append(obj)

        # Building our own index of data
        self._articles_by_id = {
            element["hash"]: element for element in indata.get("data", [])
        }

        return

    def search(self, keywords: str | list[str], num: int):
        """
        Search on the internal data base for the N best elements.
        """
        if type(keywords) == str:
            keywords = [keywords]

        if len(keywords) > 5:
            keywords = keywords[:5]

        # Fetch the N best words
        articles = self._get_best(keywords=list(keywords))

        # Sort the N best elements
        articles = sorted(articles.items(), key=lambda item: item[1], reverse=True)[
            :num
        ]

        # Get the confidence level
        confidence = self._get_confidence(articles=articles, size=len(keywords))

        # Get full data logs
        results = self._get_rich_results(articles=articles)

        # Console print:
        print(f"[LOG] Query returned : {confidence}", articles)

        # Return the N best articles
        return confidence, results

    # ------------------------------------------
    # UTILITIES
    # ------------------------------------------

    def _normalize(self, token: str) -> str:

        # First, remove any unicode elements
        token = unidecode(token)

        # Make it lower case
        return token.lower()

    def _levenshtein(self, s1: str, s2: str) -> int:

        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row: list[int] = list(range(len(s2) + 1))

        for i, c1 in enumerate(s1):
            current_row: list[int] = [i + 1]

            for j, c2 in enumerate(s2):
                insertions = current_row[j] + 1
                deletions = previous_row[j + 1] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]

    def _get_best(self, keywords: list[str]) -> dict:
        """
        Seek for the best matching articles in the list
        """

        # Iterate over the keywords
        article_scores = dict()

        for word in keywords:
            normalized = self._normalize(word)
            q_len = len(normalized)

            # exact match
            if normalized in self.keywords:
                for entry in self.keywords[normalized]:
                    if entry.hash not in article_scores:
                        article_scores[entry.hash] = [0, 0]
                    article_scores[entry.hash][0] += int(entry.score)
                    article_scores[entry.hash][1] = entry.ts

            # Iterate over the tokens
            for token, entries in self.keywords.items():
                if token == normalized:
                    continue

                coeff = 0.0

                # Inclusions
                if normalized in token:
                    coeff = 0.75

                # Typing error
                elif q_len >= 4 and abs(len(token) - q_len) <= 1:
                    if self._levenshtein(normalized, token) == 1:
                        coeff = 0.5

                if coeff > 0.0:
                    for entry in entries:
                        if entry.hash not in article_scores:
                            article_scores[entry.hash] = [0, 0]
                        article_scores[entry.hash][0] += int(entry.score * coeff)
                        article_scores[entry.hash][1] = entry.ts

        return article_scores

    def _get_confidence(
        self, articles: list[tuple[str, tuple[int, int]]], size: int
    ) -> float:
        """
        Indicate at which point we could be confident that this result is actually correct ?
        """

        # Get the highest score as possible
        score_max = 100000 * size

        # Get the total of the scores
        total = 0
        for article in articles:
            total += article[1][0]

        # Now, we can get the ratio
        conf = min(100, math.sqrt((total / score_max)) * 100)

        return round(conf, 1)

    def _get_rich_results(
        self, articles: list[tuple[str, tuple[int, int]]]
    ) -> list[dict]:
        """
        Return the raw list of elements sourced by the JSON buffer.

        The output structure is just copied from the input, to ensure
        we won't do any useless copy, and just pass the other keys.
        """

        rich = [self._articles_by_id[art_id] for art_id, _ in articles]
        return rich
