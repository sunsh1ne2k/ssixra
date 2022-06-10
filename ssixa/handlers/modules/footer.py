from tornado.web import UIModule
# from ssixa import version


class FooterModule(UIModule):

    def render(self):
        return self.render_string('modules/footer.html', version='0.0.1')
