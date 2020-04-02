from tornado.web import UIModule

class MenuModule(UIModule):

    def render(self):
        environment = self.handler.application.settings['environment']

        return self.render_string('modules/menu.html', environment=environment)