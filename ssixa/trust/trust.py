from sqlalchemy import and_
from base.database.tmdbobject import TMProvider, TMAttribute, TMDID

import logging

log = logging.getLogger(__name__)

class TrustModelBase(object):

    def acceptAttribute(self, attribute, providers):
        # Must be overwritten
        assert False

    def acceptAttributes(self, attributes, providers):
        # Must be overwritten
        assert False

class SimpleTrustModel(TrustModelBase):

    def __init__(self, trusted, debug=False):
        assert isinstance(trusted, list)

        self.trusted = trusted
        self.debug = debug

    def acceptAttribute(self, attribute, providers):
        if providers in self.trusted:
            return True
        return False

    def acceptAttributes(self, attributes, providers):
        assert isinstance(attributes, list)
        assert isinstance(providers, list)

        accept_att = []
        for a in attributes:
            if self.acceptAttribute(a, providers):
                accept_att.append(a)
        return accept_att

class AttributeAggregationTrustModel(TrustModelBase):

    def __init__(self, db, debug=False):
        self.db = db
        self.debug = debug

    def calcualateJointProbCV(self, correctness, validity, factor):
        overall = correctness * (correctness + factor * (min(1, correctness/validity-factor)))

        if self.debug:
            log.debug("Correctness: {0}, Validity: {1}, Factor: {2}, Result: {3}".format(correctness,
                    validity, factor, overall))
        return overall

    def calculateTrust(self, attribute, pro):

        s = None
        rel_prov = None
        resolved_prov = []
        for p in pro:
            resolved_prov.append(self.resolveDIDtoProvider(p.name))

        try:
            s = self.db.get_session()
            rel_prov = s.query(TMProvider).filter(and_(TMProvider.name.in_([p.name for p in resolved_prov]),
                        TMProvider.attributes.any(name=attribute.name))).all()
        except Exception as e:
            log.debug(str(e))
        finally:
            if s is not None:
                s.close()

        if s is None or rel_prov is None or len(rel_prov) == 0:
            return 0.0

        if self.debug:
            log.debug("Providers: {0}".format(str([p.name for p in rel_prov])))

        # Calculate the trust rating
        overall = 0.0
        if len(rel_prov) > 0 and len(rel_prov) < 2:
            p = rel_prov[0]
            overall = self.calcualateJointProbCV(p.correctness, p.validity, p.factor)
        else:
            p = rel_prov[0]
            overall = self.calcualateJointProbCV(p.correctness, p.validity, p.factor)
            rel_prov.remove(p)
            for p in rel_prov:
                prob1 = overall
                prob2 = self.calcualateJointProbCV(p.correctness, p.validity, p.factor)
                overall = prob1 + prob2 - prob1 * prob2

        if self.debug:
            log.debug("Overall probability: {0}".format(str(overall)))

        return overall

    def acceptAttribute(self, attribute, providers):
        assert isinstance(attribute, TMAttribute)

        s = None
        att = None
        try:
            s = self.db.get_session()
            att = s.query(TMAttribute).filter(TMAttribute.name==attribute.name).all()
        except Exception as e:
            log.error(str(e))
        finally:
            s.close()

        if att is None or len(att)==0:
            return False

        if att[0].acceptance < self.calculateTrust(att[0], providers):
            return True
        else:
            return False

    def acceptAttributes(self, attributes, providers):
        assert isinstance(attributes, list)
        assert isinstance(providers, list)

        accept_att = []
        for a in attributes:
            if self.acceptAttribute(a, providers):
                accept_att.append(a)
        return accept_att

    def resolveDIDtoProvider(self, did):
        d = TMDID(did)

        s = None
        prov = None
        try:
            s = self.db.get_session()
            prov = s.query(TMProvider).filter(TMProvider.dids.any(did=d.did)).all()

            if len(prov) == 1:
                if self.debug:
                    log.debug("Provider: {0}".format(prov[0].name))
                return prov[0]
            elif len(prov) > 1:
                if self.debug:
                    log.debug("Providers: {0}".format(str([p.name for p in prov])))
                raise DIDNotUniqueException("DID not unique: " + did)
            else:
                return None
        except Exception as e:
            log.error(str(e))
        finally:
            if s is not None:
                s.close()

        return None

class DIDNotUniqueException(Exception):
    pass