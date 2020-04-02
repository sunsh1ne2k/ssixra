from ssixa.base.verification.verificationbase import VerificationMethodBase, RequiredClaimMissingException
from oic.oic import rndstr

import ldap3
import datetime
import logging

log = logging.getLogger(__name__)

class LDAPVerification(VerificationMethodBase):
    required_claims = []
    claim=""
    name=""
    description=""

    def __init__(self, baseurl, cfg):
        super(LDAPVerification, self).__init__(baseurl, cfg)

        self.db = {}

        self.protocol = cfg['protocol']
        self.server = cfg['server']
        self.port = cfg['port']
        self.basedn = cfg['basedn']

        self.ttl = 30

    def __call__(self, username, password):
        log.debug("Query against " + username)

        self.db[username] = dict(
            name='',
            start=datetime.datetime.now(),
            verified=False
        )

        result = self.execute_ldap_query(username, password, 'name')
        if not result is None:
            self.db[username]['name'] = result
            self.db[username]['verified'] = True

    def execute_ldap_query(self, username, password, attribute):
        log.debug("Query ldap {0} for attribute {1}", username, attribute)
        conn = ldap3.Connection(self.server, user=username, password=password)
        result = conn.bind()
        if result:
            log.debug("Bind successful")
            conn.search(self.basedn, '(objectClass=*)', attributes=ldap3.ALL_ATTRIBUTES)
            if len(conn.entries) != 1:
                log.debug("Found less/ more than one entry: " + str(len(conn.entries)))
            entry = conn.entries[0]

            return entry.displayname.value
        return None

    def verification_completed(self, username):
        if username not in self.db:
            return False

        if self.db[username]['verified'] == True:
            return True
        else:
            return False

    def get_claim_value(self, username):
        if username not in self.db:
            return None

        if self.db[username]['verified'] == False:
            return None

        return self.db[username]['name']