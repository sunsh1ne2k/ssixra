from ssixa.app import SSIXA
from tornado.testing import AsyncHTTPTestCase, bind_unused_port
from tornado.httpserver import HTTPServer

# Port needs to be provided for SSIXA, but test cases run on random port
app = SSIXA('test_config.yaml',port=80)


class TestHandlerBase(AsyncHTTPTestCase):
    def setUp(self):
        super(TestHandlerBase, self).setUp()

        server = HTTPServer(app)
        socket, self.port = bind_unused_port()
        server.add_socket(socket)

    def get_app(self):
        return app




