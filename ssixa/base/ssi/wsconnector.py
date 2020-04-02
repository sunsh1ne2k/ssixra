import logging
import requests

log = logging.getLogger(__name__)


class WSConnector(object):

    def __init__(self, url, app):
        self.url = str(url)
        self.app = str(app)

    def createChallenge(self, **params):
        raise Exception("Not implemented")

    def verifyChallenge(self, **params):
        raise Exception("Not implemented")

    def createAttestedClaim(self, **params):
        raise Exception("Not implemented")

    def executeWSCall(self, relPath, **kwargs):

        response = None
        try:
            response = requests.get("{0}/{1}".format(self.url, relPath),params=kwargs)
        except Exception as e:
            log.exception("Web service call failed.")

        if not response is None and response.status_code == 200:
            log.debug("Status received: " + str(response.status_code))
            log.debug(response.content)
            return response.content.decode()
        else:
            log.error("Received error code from web service: " + str(response))
            return None