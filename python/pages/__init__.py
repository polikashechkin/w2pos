from domino.pages import Page as BasePage
from domino.core import log

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)
        self.postgres = None
        self.oracle  = None
