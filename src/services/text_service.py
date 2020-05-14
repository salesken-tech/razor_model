from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
import nltk
from src.utilities import sken_logger, constants, sken_exceptions
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob

ps = PorterStemmer()
lemmatizer = WordNetLemmatizer()

logger = sken_logger.get_logger("text_service")

not_accepted_pos = ["DT", "VBZ", "PRP", "VBP", "MD", "VB", "IN"]


def get_tokens(sentence):
    """
    This method produces the tokens from a sentence
    :param sentence:
    :return: token list
    """
    return word_tokenize(sentence)


def get_synonyms(sentence):
    """
    This method breaks the sentence into tokens and gets the pos tags for them if the pos tag is not in the list of
    restricted token list it gets the synonyms for each token using any of the three methods
    @param sentence:
    @return:
    """
    global not_accepted_pos
    if len(sentence.split()) > 0:
        tokens = get_tokens(sentence)
        logger.info("Made {} tokens for {}".format(len(tokens), sentence))
        pos_tags = nltk.pos_tag(tokens)
        result = []
        for tag in pos_tags:
            if tag[1] not in not_accepted_pos:
                result.append(get_synonyms_thesaurus(tag[0], int(constants.fetch_constant("max_synonims"))))
            else:
                result.append({tag[0]: []})

        max_length = max([len(list(item.values())[0]) for item in result])
        return {"data": result, "max_len": max_length}
    else:
        raise sken_exceptions.NoTokensFound


def get_synonyms_thesaurus(word, max_synonims):
    """
    This method fetches the synonyms from  www.thesaurus.com site using web-scraping
    @param word:
    @param max_synonims:
    @return: list of synonym for the given word
    """
    logger.info("Getting thesaurus synonims for {}".format(word))
    response = requests.get("https://www.thesaurus.com/browse/{}".format(word))
    soup = BeautifulSoup(response.content, 'html.parser')
    x = soup.find('section', {'class': 'MainContentContainer'}).find_all("div")
    synonym_div = []
    for div in x:
        for h in div.find_all("h2"):
            if "Synonyms" in h.text:
                synonym_div.append(div)
    synonyms = set()
    for div in synonym_div:
        for span in div.find_all("span"):
            for a in span.find_all("a"):
                synonyms.add(a.text)
    return {
        word: list(synonyms)[:max_synonims] if len(list(synonyms)) > max_synonims else list(synonyms)}


def sentence_breaker(sentence):
    """
    This method extracts all the sentences present in a single long sentence using TextBlob
    @param sentence: str
    @return: list of sentences present
    """
    if len(sentence.split()) > 0:
        testimonial = TextBlob(sentence)
        sentences = []
        for sent in testimonial.sentences:
            sentences.append(str(sent))
        return sentences


def make_root_word(token_list):
    global ps, lemmatizer
    tokens = nltk.pos_tag(token_list)
    root_tokens = []
    for token in tokens:
        if "VB" in token[1]:
            root_tokens.append(ps.stem(token[0]))
        else:
            root_tokens.append(lemmatizer.lemmatize(token[0]))
    return root_tokens
