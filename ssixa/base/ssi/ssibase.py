from oic.oic import rndstr

import logging

log = logging.getLogger(__name__)


class BaseSSI(object):
    name=''
    default_config=dict()

    def __init__(self):
        pass

    def testConnection(self):
        pass

    def resolveIdentity(self):
        pass

    def buildDIDdocument(self):
        pass

    def updateConfig(self, default, config):
        if self.name in config:
            default[self.name].update(config[self.name])
        config[self.name] = default[self.name]
        return config

    def createChallenge(self, cb, scope=None):
        # To be implemented for subclasses
        raise Exception("Not implemented")

    def verifyChallenge(self, response):
        # To be implemented for subclasses
        raise Exception("Not implemented")

    def createAttestedClaim(self, subject, name, value):
        # To be implemented for subclasses
        raise Exception("Not implemented")