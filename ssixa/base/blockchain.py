from oic.utils.authn.user import UserAuthnMethod as OIDCUserAuthnMethod
from saml2.authn import UserAuthnMethod as SAMLUserAuthnMethod
from oic.utils.http_util import Redirect
from ssixa.base.ssi.uport import UPort
from ssixa.base.ssi.jolocom import Jolocom
from ssixa.base.ssi.lissi import Lissi

import datetime
import json
import logging

log = logging.getLogger(__name__)


class BlockchainAuthMethod(OIDCUserAuthnMethod, SAMLUserAuthnMethod):
    acr = 'blockchain'

    rel_urls = dict(
        url_createchallenge = "/blockchain/challenge",
        url_verify = "/blockchain/verification",
        url_verify_sidechannel = "/blockchain/verificationside",
        url_statusverification = "/blockchain/statusverification")

    def __init__(self, baseurl, proxymode, config, userinfodb, trustmodel):
        super(BlockchainAuthMethod, self).__init__(None)

        # Extend entry points with base url
        self.urls = dict()
        if proxymode:
            urlparts = baseurl.split(':')
            self.urls['url_statusverification'] = urlparts[0] + ':' + urlparts[1] + self.rel_urls['url_statusverification']
        else:
            self.urls['url_statusverification'] = baseurl + self.rel_urls['url_statusverification']
            self.urls['url_createchallenge'] = baseurl + self.rel_urls['url_createchallenge']
            self.urls['url_verify'] = baseurl + self.rel_urls['url_verify']

        # Sidechannel incl. port that the right web server is found by smartphone connection
        self.urls['url_verify_sidechannel'] = baseurl + self.rel_urls['url_verify_sidechannel']

        # Replace protocol for status verification url
        if "https" in self.urls['url_statusverification']:
            self.urls['url_statusverification'] = self.urls['url_statusverification'].replace("https","wss")
        elif "http" in self.urls['url_statusverification']:
            self.urls['url_statusverification'] = self.urls['url_statusverification'].replace("http", "ws")

        self.codes = dict()

        # Add all SSI solutions here
        self.ssi = dict()
        if 'uport' in config['authmethodcfg']:
            self.ssi['uport']=UPort(config['authmethodcfg']['uport'], trustmodel)
            log.debug("UPort added to blockchain authentication")
        if 'jolocom' in config['authmethodcfg']:
            self.ssi['jolocom']=Jolocom(config['authmethodcfg']['jolocom'], baseurl, trustmodel)
            log.debug("Jolocom added to blockchain authentication")
        if 'lissi' in config['authmethodcfg']:
            self.ssi['lissi']=Lissi(config['authmethodcfg']['lissi'], trustmodel)
            log.debug("Lissi added to blockchain authentication")

        self.default_ssi = config['authmethodcfg']['default']
        log.debug("Default SSI solution " + str(self.default_ssi))
        self.code_ttl = config['oidc_config']['code_ttl']

        # Store reference to user info db
        self.userinfodb = userinfodb

        self.status_callbacks = dict()

    def __call__(self, *args, **kwargs):
        log.debug("Start new authentication")

        # Redirect to the create challenge entry point
        if "key" in kwargs:
            return Redirect("{0}?key={1}".format(self.urls['url_createchallenge'],kwargs["key"]))
        else:
            return Redirect("{0}?".format(self.urls['url_createchallenge']))

    def create_challenge(self, ssi, claims, client_id=None):
        log.debug("challenge created")

        if ssi not in self.ssi:
            log.error("Requested SSI not available.")
            raise SSINotFoundException()

        # Create challenge structure
        random, challenge =  self.ssi[ssi].createChallenge(self.urls['url_verify_sidechannel'], claims)

        pollurl = "{0}/{1}".format(self.urls['url_statusverification'],random)

        # Add code
        self.codes[random] = dict(time=datetime.datetime.now(),
                                verified=False,
                                name='',
                                requested_claims=claims,
                                info='',
                                ssi=ssi,
                                client=client_id)

        # Add statistics of created challenge
        if not self.srv is None:
            self.srv.statlogger.log("challenge_created",ssi,"")

        return dict(
                challenge=challenge,
                random=random,
                url_verify="{0}/{1}".format(self.urls['url_verify'],random),
                url_poll=pollurl)


    def verify(self, random):
        log.debug("authn verification")

        if (random in self.codes) and (self.codes[random]['verified'] == True):
            return self.codes[random]['name']

    def verify_sidechannel(self, rand, token):
        log.debug("authn side channel verification")

        tk = ""
        if "access_token" in token:
            tk = token["access_token"]
        elif "token" in token:
            tk = token["token"]
        else:
            return

        if rand in self.codes:
            if self.codes[rand]['time'] + datetime.timedelta(minutes=self.code_ttl) > datetime.datetime.now():
                info = self.ssi[self.codes[rand]["ssi"]].verifyChallenge(tk)

                if info is not None and 'id' in info:
                    log.debug(json.dumps(info))
                    self.userinfodb.add_claims(info['id'], info, self.codes[rand]['client'])

                    self.codes[rand]['name'] = info['id']
                    self.codes[rand]['info'] = info
                    self.codes[rand]['verified'] = True

                    # Add statistics of successful authentication
                    if not self.srv is None:
                        self.srv.statlogger.log("successful_authentication",self.codes[rand]['ssi'] + "|" + self.codes[rand]['name'], "")

                    # Notify status callbacks
                    if rand in self.status_callbacks:
                        self.status_callbacks[rand]("verified")

    def get_available_ssi(self):
        return list(self.ssi.keys())

    def get_default_ssi(self):
        return self.default_ssi

    def register_statuscallback(self, rand, function):
        self.status_callbacks[rand] = function

    def unregister_statuscallback(self, rand, function):
        del self.status_callbacks[rand]


class SSINotFoundException(Exception):
    pass