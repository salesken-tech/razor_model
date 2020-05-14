class VadChunk(object):
    """
    Represents the snippet object
    """

    def __init__(self, sid, from_time, to_time, speaker, text, task_id, old_snippet_list,
                 questions=None):
        self.sid = sid
        self.from_time = from_time
        self.to_time = to_time
        self.speaker = speaker
        self.text = text
        self.task_id = task_id
        self.old_snippet_list = old_snippet_list
        self.questions = questions


class Signal(object):
    """
    Represents the signals
    """

    def __init__(self, sid, threshold, token_df, value, html_text):
        self.sid = sid
        self.threshold = threshold
        self.token_df = token_df
        self.value = value
        self.html_text = html_text

    def set_threshold(self, threshold):
        self.threshold = threshold

    def set_token_df(self, token_df):
        self.token_df = token_df


class Match(object):
    """
    Represent the matched object
    """

    def __init__(self, snippet_id, signal_id, snippet_text, signal_text, matched_tokens, score, threshold, snippet,
                 signal):
        self.snippet_id = snippet_id
        self.signal_id = signal_id
        self.snippet_text = snippet_text
        self.signal_text = signal_text
        self.matched_tokens = matched_tokens
        self.score = score
        self.threshold = threshold
        self.snippet = snippet
        self.signal = signal
