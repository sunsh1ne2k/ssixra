import tornado.web
import tornado.websocket
import logging

logger = logging.getLogger(__name__)


class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        user_cookie = self.get_secure_cookie("user")

        if (self.settings["environment"] == "dev" or self.settings["environment"] == "test") and self.settings["protocol"] == "http":
            user_cookie = self.get_cookie("user")
            if user_cookie is not None:
                user_cookie = user_cookie.encode()

        if user_cookie:
            return user_cookie.decode("utf-8")
        return None

    def head(self):
        self.write("")

class BaseWebSocketHandler(tornado.websocket.WebSocketHandler):
    pass