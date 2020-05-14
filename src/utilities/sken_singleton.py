from src.utilities import sken_logger

import spacy
from spacy.matcher import PhraseMatcher

logger = sken_logger.get_logger("Singleton")


#

class Singletons:
    __instance = None
    cached_signals = phrase_matcher = nlp = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if Singletons.__instance is None:
            logger.info("Calling Singletone private constructor")
            Singletons()
        return Singletons.__instance

    def __init__(self):
        if Singletons.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            logger.info("Creating empty cache for signals")
            self.cached_signals = {}
            logger.info("Making the question PhraseMatcher")
            self.nlp = spacy.load("en_core_web_sm")
            self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr='LOWER')
            question_terms = ["who", "whom", "whose", "what", "when", "where", "why", "which", "how"]
            patterns = [self.nlp(text) for text in question_terms]
            self.phrase_matcher.add("question", None, *patterns)
            Singletons.__instance = self

    def get_cached_signals(self):
        """
        This method gets the cached signal dict
        @return: signal dict format {"prod_id":[list of signal object]}
        """
        return self.cached_signals

    def set_cached_signals(self, product_id, signals):
        if str(product_id) not in self.cached_signals.keys():
            self.cached_signals[str(product_id)] = signals
        return self.cached_signals

    def get_phrase_matcher(self, doc):
        return self.phrase_matcher(doc)

    def return_nlp(self, sentence):
        return self.nlp(sentence)
