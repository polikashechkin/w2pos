from . import Page as BasePage, log

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)

    def __call__(self):
        pass
