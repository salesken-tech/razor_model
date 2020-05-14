class SkenException(Exception):
    pass


class NoTokensFound(SkenException):
    def __init__(self):
        self.code = 31001
        self.message = "No tokens found"


class NoSignalFound(SkenException):
    def __init__(self, prod_id, task_id):
        self.code = 31002
        self.message = "No signal found for task_id={} and prod_id ={} for Razor model".format(task_id, prod_id)


class NoProductFound(SkenException):
    def __init__(self, task_id):
        self.code = 31002
        self.message = "No Product found for task_id={} for Razor model".format(task_id)
