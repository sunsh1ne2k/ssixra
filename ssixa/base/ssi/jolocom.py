from ssixa.base.ssi.ssibase import BaseSSI
from ssixa.trust.trust import TMAttribute, TMProvider
from ssixa.base.ssi.wsconnector import WSConnector
from oic.oic import rndstr

import jwt
import json
import datetime
import logging

log = logging.getLogger(__name__)


class Jolocom(BaseSSI):
    name='jolocom'
    didpattern='did:jolo'

    url_receive='/claims/jolocom'

    def __init__(self, config, baseurl=None, trustmodel=None):
        super(BaseSSI, self).__init__()

        self.comm = JolocomWS(config['proxy_url'], config['appname'], config['passphrase'], config['seed'])
        self.appid = config['appid']
        self.trustmodel = trustmodel

        self.offeredCredentials=dict()
        self.credentialToRandom=dict()

        if baseurl is not None:
            self.url_receive = baseurl + self.url_receive


    def createChallenge(self, callback, claims=None):
        log.debug("Callback: " +str(callback))
        log.debug("Claims: " + str(claims))

        random = rndstr(17)

        credentials = []
        for c in claims:
            if c in claim2jolocom:
                credentials.append(claim2jolocom[c])
        log.debug("Credentials: " + str(credentials))

        challenge = self.comm.createChallenge('{0}/{1}'.format(callback,random) , credentials)

        log.debug("Random: " + str(random))
        log.debug("Challenge: " + str(challenge))

        if not challenge is None:
            return random, challenge
        else:
            return None, None

    def verifyChallenge(self, token, test=False):
        log.debug("Token: " + str(token))
        log.debug("Testmode: " +str(test))

        if test or self.comm.verifyChallenge(token):

            if test:
                decoded_token = json.loads(token)
            else:
                decoded_token = jwt.decode(token,verify=False)

            attributes = dict()
            inv_claim2jolocom = {v: k for k, v in claim2jolocom.items()}
            if decoded_token is not None:
                attributes['ssi'] = self.name
                attributes['id'] = decoded_token['iss'].split("#")[0]

                for credential in decoded_token['interactionToken']['suppliedCredentials']:
                    # Check for each credential if verified or not - actually are credentials
                    # and verifier must be retrieved and then the trust model should be applied
                    type_list = []
                    for t in credential['type']:
                        if t != "Credential":
                            type_list.append(TMAttribute(inv_claim2jolocom[t]))
                    accepted_list = self.trustmodel.acceptAttributes(type_list, [TMProvider(credential['issuer'])])
                    if accepted_list and len(accepted_list) > 0:
                        for c in credential['claim']:
                            if c in jolocom2claim:
                                attributes[jolocom2claim[c]] = credential['claim'][c]
                    else:
                        for c in credential['claim']:
                            if c in jolocom2claim:
                                attributes[jolocom2claim[c] + '_unverified'] = credential['claim'][c]

            log.debug("Attributes: " + str(attributes))
            return attributes

    def createAttestedClaim(self, subject, name, value):
        log.debug("Subject: " + str(subject))
        log.debug("Name: " + str(name))
        log.debug("Value: " + str(value))

        key = subject+name+str(value)
        token = None

        if (not key in self.credentialToRandom):
            random = rndstr(17)

            token = self.comm.createCredentialOffer('{0}/{1}'.format(self.url_receive,random))

            self.offeredCredentials[random]=dict(
                subject=subject,
                name=name,
                value=value,
                time=datetime.datetime.now()
            )
            self.credentialToRandom[key]=random


        if type(token) is not str:
            raise Exception("String expected")

        log.debug("Token: " + str(token))
        return token

    def receiveCredentialOfferResponse(self, random, token):
        log.debug("Random: " + str(random))
        log.debug("Token: " + str(token))

        if random in self.offeredCredentials:
            token = self.comm.createAttestedClaim(
                        self.offeredCredentials[random]["subject"],
                        self.offeredCredentials[random]["name"],
                        self.offeredCredentials[random]["value"],
                        json.loads(token)['token'])

            return token


class JolocomWS(WSConnector):

    def __init__(self, proxy_url, app, passphrase, seed):
        super(JolocomWS, self).__init__(proxy_url, app)

        self.passphrase = str(passphrase)
        self.seed = str(seed)

    def createChallenge(self, callback, claims):
        result = self.executeWSCall('requestcredential',
                        passphrase=self.passphrase,
                        seed=self.seed,
                        credentials=json.dumps(claims),
                        callback=callback)
        try:
            return json.loads(result)['jwt']
        except Exception as e:
            log.exception("Jolocom WS Call for Create Challenge failed")

    def verifyChallenge(self, token):
        result = self.executeWSCall('verifycredential',
                                 passphrase=self.passphrase,
                                 seed=self.seed,
                                 claims=token)
        if result is not None and result.rstrip() == 'Ok':
            return True
        else:
            return False

    def createCredentialOffer(self, callback):
        result = self.executeWSCall('createcredentialoffer',
                                 passphrase=self.passphrase,
                                 seed=self.seed,
                                 callback=callback)
        try:
            return json.loads(result)['jwt']
        except Exception as e:
            log.error("Jolocom WS Call for Create Credential Offer failed")

    def createAttestedClaim(self, subject, name, value, token):
        result = self.executeWSCall('createAttestedClaim',
                                 passphrase=self.passphrase,
                                 seed=self.seed,
                                 subject=subject,
                                 name=name,
                                 value=value,
                                 offer_response=token)
        try:
            return json.loads(result)['jwt']
        except Exception as e:
            log.error("Jolocom WS Call for Create Attested Claim failed")



claim2jolocom=dict(
    email='ProofOfEmailCredential',
    name='ProofOfNameCredential',
    firstname='ProofOfFirstnameCredential',
    lastname='ProofOfLastnameCredential',
)

jolocom2claim=dict(
    familyName='lastname',
    givenName='firstname',
    email='email',
    name='name'
)