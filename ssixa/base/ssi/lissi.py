from ssixa.base.ssi.ssibase import BaseSSI
from oic.oic import rndstr
from ssixa.trust.trust import TMAttribute, TMProvider

import requests
import json
import copy
import sys
import random
import logging

try:
    from indy.libindy import _cdll
    _cdll()
except ImportError:
    print("python3-indy module not installed")
    sys.exit(1)
except OSError:
    print("libindy shared library could not be loaded")
    sys.exit(1)

log = logging.getLogger(__name__)

###################################################
# Experimential HyperLedger Indy Integration/Aries
# based on the Lissi Project
# ACA-Py client needs to be available
###################################################


class Lissi(BaseSSI):
    name='lissi'
    didpattern=['did:lissi']

    def __init__(self, config, trustmodel):
        super(BaseSSI, self).__init__()

        self.acapy_admin_url = config['acapy_admin_url']
        self.acapy_inbound_url = config['acapy_inbound_url']
        self.did_autocreate = config['did_autocreate']

        # Instantiate DID for SSIXA
        self.did = config['did']
        if self.did is None:
            self.did = self.get_public_did()
        if self.did is None and self.did_autocreate:
            log.info("No DID available, create new public DID")
            self.register_did()
            self.did = self.get_public_did()
        assert self.did is not None

        # Instantiate schema and credential definition for SSIXA
        self.schema_id = config['schema_id']
        self.credential_def_id = config['cred_def_id']
        self.schema_version = config['schema_version']

        # Create schema and definition if no is available
        if self.schema_id is None or self.credential_def_id is None or self.schema_version is None:
            self.schema_version = format("%d.%d.%d"%(random.randint(1, 101), random.randint(1, 101),random.randint(1, 101)))
            self.schema_id, self.credential_def_id = self.register_schema_and_creddef(
                    "person data schema", self.schema_version, ["name", "email", "firstname", "lastname"])
        assert self.schema_id is not None
        assert self.schema_version is not None
        assert self.credential_def_id is not None

        self.connections = {}

        self.trustmodel = trustmodel

    def createChallenge(self, callback, claims=None):
        random = None
        challenge = None

        data = {"alias": "SSIXA", "accept": "auto"}
        try:
            resp = requests.post(self.acapy_admin_url + "/connections/create-invitation", data=json.dumps(data), headers={"accept": "application/json"})
            if resp.status_code == 200:
                if resp.content is not None:
                    content = json.loads(resp.content.decode("utf-8"))
                    challenge = content["invitation_url"]
                    random = content["connection_id"]
            else:
                log.error("Web service call to ACA-Py to create invitation failed")
        except Exception as ex:
            log.error(str(ex))

        self.connections[random] = {}
        return random, challenge

    def verifyChallenge(self, token, test=False):
        # ToDo
        #data  = self.cmd.verifyChallenge(token, test)
        #if data:
        #    attributes = dict()#

            # Special attributes - set by gateway
        #    attributes['ssi'] = self.name
        #    attributes['id'] = data['did']

            # Unverified provided attributes - all attributes at the top-level except verified, invalid
        #    for attr in data:
        #        if attr in ['verified','invalid']:
        #            continue
        #        if attr in uport_property_list:
        #            attributes[attr+'_unverified'] = data[attr]
        #        else:
        #            attributes[attr] = data[attr]

            # Verified provided list of attributes
        #    if 'verified' in data:
        #        # Iterate over all provided verified data structures
        #        for ver in data['verified']:
        #            sub = ver['sub']
        #            iss = ver['iss']

        #            if 'claim' in ver:
        #                # Iterate over all provided claims
        #                for att_ver in ver['claim']:
        #                    if self.trustmodel.acceptAttributes([TMAttribute(att_ver)], [TMProvider(iss)]):
         #                       attributes[att_ver] = ver['claim'][att_ver]
        #                    else:
        #                        attributes[att_ver + '_unverified'] = ver['claim'][att_ver]

        #    return attributes
        pass

    def createAttestedClaim(self, subject, name, value):
        #ToDo
        pass
        #prefix = "me.uport:add?attestations="

        #claim_token = self.cmd.createAttestedClaim(subject, name, value)

        #return prefix + claim_token

    def get_public_did(self):
        data = {"public": True}
        try:
            resp = requests.get(self.acapy_admin_url + "/wallet/did", data=json.dumps(data), headers={"accept": "application/json"})
            if resp.status_code == 200:
                if resp.content is not None:
                    dids = json.loads(resp.content.decode("utf-8"))["results"]
                    # Check if public dids exists and take the first public did
                    if len(dids)>0:
                        return dids[0]["did"]
            else:
                log.error("Web service call to ACA-Py to retrieve DID failed")
        except Exception as ex:
            log.error(str(ex))

    def register_did(self, alias: str = None):
        # Check if public DID already exists
        pub_did = self.get_public_did()
        if pub_did is not None:
            log.error("Public did already exists")
            return

        # Create local DID in Wallet
        local_did = None
        try:
            resp = requests.post(self.acapy_admin_url + "/wallet/did/create", headers={"accept": "application/json"})
            if resp.status_code == 200:
                if resp.content is not None:
                    created_dids = json.loads(resp.content.decode("utf-8"))["results"]
                    # Check if content exists and take the first DID record
                    if len(created_dids) > 0:
                        local_did = created_dids[0]
            else:
                log.error("Web service call to ACA-Py to create local DID failed")
        except Exception as ex:
            log.error(str(ex))

        # Write local DID to ledger
        data = {"did": local_did["did"], "verkey": local_did["verkey"], "role": "TRUST_ANCHOR"}
        try:
            resp = requests.post(self.acapy_admin_url + "/ledger/register-nym", data=json.dumps(data), headers={"accept": "application/json"})
            if resp.status_code != 200:
                log.error("Web service call to ACA-Py to create local DID failed")
        except Exception as ex:
            log.error(str(ex))

        # Make DID public in wallet
        data = {"did": local_did["did"]}
        try:
            resp = requests.post(self.acapy_admin_url + "/wallet/did/public", data=json.dumps(data), headers={"accept": "application/json"})
            if resp.status_code != 200:
                log.error("Web service call to ACA-Py to create local DID failed")
        except Exception as ex:
            log.error(str(ex))

    def register_schema_and_creddef(self, schema_name, version, schema_attrs):
        schema_id = None
        cred_id = None

        # Create a schema
        data = {"schema_name": schema_name, "schema_version": version, "attributes": schema_attrs}
        try:
            resp = requests.post(self.acapy_admin_url + "/schemas", data=json.dumps(data), headers={"accept": "application/json"})
            if resp.status_code == 200:
                if resp.content is not None:
                    created_schema = json.loads(resp.content.decode("utf-8"))
                    # Check if content exists and take the first DID record
                    if len(created_schema) > 0:
                        schema_id = created_schema["schema_id"]
            else:
                log.error("Web service call to ACA-Py to create schema failed")
        except Exception as ex:
            log.error(str(ex))

        # Create a cred def for the schema
        data = {"schema_id": schema_id}
        try:
            resp = requests.post(self.acapy_admin_url + "/credential-definitions", data=json.dumps(data), headers={"accept": "application/json"})
            if resp.status_code == 200:
                if resp.content is not None:
                    created_cred = json.loads(resp.content.decode("utf-8"))
                    # Check if content exists and take the first DID record
                    if len(created_cred) > 0:
                        cred_id = created_cred["credential_definition_id"]
            else:
                log.error("Web service call to ACA-Py to create schema failed")
        except Exception as ex:
            log.error(str(ex))

        return schema_id, cred_id

    def retrieve_credentials(self, connection_id, claims):
        # ToDo

        data = {"connection_id": connection_id,
                "comment": "SSIXA requests attributes",
                "proof_request": {
                    "version": "1.0",
                    "name": "Proof request",
                    "nonce": rndstr(10),
                    "requested_attributes": {
                        "additionalProp1": {
                            "restrictions": [{
                                "credential_definition_id": self.credential_def_id,
                                "schema_issuer_did": self.did,
                                "schema_version": self.schema_version,
                                "cred_def_id": self.credential_def_id,
                                "schema_id": self.schema_id,
                                "issuer_did": self.did,
                                "schema_name": "transcript"}],
                            "non_revoked": {
                                "from_epoch": 1577620743,
                                "to_epoch": 1577620743},
                        "name": "email"}}}
                }

        try:
            resp = requests.post(self.acapy_admin_url + "/present-proof/send-request", data=json.dumps(data), headers={"accept": "application/json"})
            if resp.status_code == 200:
                if resp.content is not None:
                    test = json.loads(resp.content.decode("utf-8"))
            else:
                log.error("Web service call to ACA-Py to retrieve credential proof failed")
        except Exception as ex:
            log.error(str(ex))

lissi_property_list = ['email','name','firstname','lastname']