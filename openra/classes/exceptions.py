from typing import List


class ExceptionBase(Exception):

    message: str
    friendly: str
    detail: List[str]

    def __init__(self):
        self.message = ''
        self.detail = []
        self.friendly = 'An error occurred, please try again later'

    def get_full_details(self):
        buffer = 'User Message: ' + self.friendly
        buffer += '\n\n'
        buffer += 'Error: ' + self.message
        buffer += '\n\n'
        buffer += 'Additional Details:\n'
        for line in self.detail:
            buffer += line + '\n'
        return buffer

    def print_full_details(self):
        print(self.get_full_details())
