from tornado.web import UIModule

class HeaderModule(UIModule):

    def render(self):
        return self.render_string('modules/header.html')