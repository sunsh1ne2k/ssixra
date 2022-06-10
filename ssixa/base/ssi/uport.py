from base.ssi.ssibase import BaseSSI
from oic.oic import rndstr
from jwt.algorithms import ECAlgorithm
from trust.trust import TMAttribute, TMProvider
from base.ssi.wsconnector import WSConnector

import jwt
import json
import copy
import logging

log = logging.getLogger(__name__)


class UPort(BaseSSI):
    name='uport'
    didpattern=['did:uport','did:ethr']

    def __init__(self, config, trustmodel):
        super(BaseSSI, self).__init__()

        # Setup jwt ES256K algorithm for token decoding verification and encoding
        try:
            jwt.register_algorithm('ES256K', ECAlgorithm(ECAlgorithm.SHA256))
        except ValueError as ve:
            log.debug(str(ve))

        self.comm = uPortWS(config['proxy_url'], config['appname'], config['appid'], config['key'])
        self.appid = config['appid']
        self.trustmodel = trustmodel

    def createChallenge(self, callback, claims=None):
        log.debug("Callback: " + callback)
        log.debug("Claims: " + str(claims))

        prefix = "me.uport:me?requestToken="

        random = rndstr(17)

        # Get all required claims whether they are verified or self-signed
        # No differeniation is made
        claims.append('email')
        credentials = copy.copy(claims)
        credentials_verified = copy.copy(claims)

        log.debug("Credentials: " + str(credentials))
        log.debug("Credentials verified: " + str(credentials_verified))

        challenge = self.comm.createChallenge('{0}/{1}'.format(callback,random), credentials, credentials_verified)

        log.debug("Random: " + str(random))
        log.debug("Prefix: " + str(prefix))
        log.debug("Challenge: " + str(challenge))

        if not challenge is None:
            return random, prefix + challenge
        else:
            return None, None

    def verifyChallenge(self, token, test=False):
        log.debug("Token: " + token)
        log.debug("Testmode: " +str(test))

        data  = self.comm.verifyChallenge(token, test)
        if data:
            attributes = dict()

            # Special attributes - set by gateway
            attributes['ssi'] = self.name
            attributes['id'] = data['did']

            # Unverified provided attributes - all attributes at the top-level except verified, invalid
            for attr in data:
                if attr in ['verified','invalid']:
                    continue
                if attr in uport_property_list:
                    attributes[attr+'_unverified'] = data[attr]
                else:
                    attributes[attr] = data[attr]

            # Verified provided list of attributes
            if 'verified' in data:
                # Iterate over all provided verified data structures
                for ver in data['verified']:
                    sub = ver['sub']
                    iss = ver['iss']

                    if 'claim' in ver:
                        # Iterate over all provided claims
                        for att_ver in ver['claim']:
                            if self.trustmodel.acceptAttributes([TMAttribute(att_ver)], [TMProvider(iss)]):
                                attributes[att_ver] = ver['claim'][att_ver]
                            else:
                                attributes[att_ver + '_unverified'] = ver['claim'][att_ver]

            log.debug("Attributes: " + str(attributes))
            return attributes

    def createAttestedClaim(self, subject, name, value):
        log.debug("Subject: " + str(subject))
        log.debug("Name: " + str(name))
        log.debug("Value: " + str(value))

        prefix = "me.uport:add?attestations="

        claim_token = self.comm.createAttestedClaim(subject, name, value)

        log.debug("Prefix: " + str(prefix))
        log.debug("Claim token: " + str(claim_token))
        return prefix + claim_token

uport_property_list = ['email','name','firstname','lastname']

class uPortWS(WSConnector):

    def __init__(self, proxy_url, appname, appid, key):
        super(uPortWS, self).__init__(proxy_url, appname)

        self.appid = str(appid)
        self.key = str(key)

    def createChallenge(self, callback, claims, claims_verified):
        result = self.executeWSCall('requestcredential',
                                appname=self.app,
                                did=self.appid,
                                privatekey=self.key,
                                claims=json.dumps(claims),
                                claims_verified=json.dumps(claims_verified),
                                callback=callback)

        try:
            return json.loads(result)['jwt']
        except Exception as e:
            log.exception("uPort WS Call for Create Challenge failed")

    def verifyChallenge(self, token, test):
        if not test:
            result = self.executeWSCall('verifycredential',
                                appname=self.app,
                                did=self.appid,
                                privatekey=self.key,
                                token=token)
        else:
            result = token

        try:
            return json.loads(result)['jwt']
        except Exception as e:
            log.exception("uPort WS Call for Verify Challenge failed")

    def createAttestedClaim(self, subject, name, value):
        result = self.executeWSCall('createattestedclaim',
                                    appname=self.app,
                                    did=self.appid,
                                    privatekey=self.key,
                                    subject=subject,
                                    name=name,
                                    value=value)

        try:
            return json.loads(result)['jwt']
        except Exception as e:
            log.exception("uPort WS Call for Create Attested Claim failed")