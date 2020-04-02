from ssixa.base.database.basedb import SSIXADBBase
from ssixa.base.database.tmdbobject import TMProvider, TMAttribute, TMDID

import logging
log = logging.getLogger(__name__)

class TrustModelDB(SSIXADBBase):

    def __init__(self, db, debug=False):
        SSIXADBBase.__init__(self, db)

    def add_update_attribute(self, name, acceptance):
        log.debug("Name: " + name)
        log.debug("Acceptance: " + str(acceptance))
        s = None
        try:
            s = self.get_session()
            atts = s.query(TMAttribute).filter(TMAttribute.name==name).all()
            if atts is not None and len(atts) == 1:
                # Attribute exists; just acceptance rate will be updated
                atts[0].acceptance = acceptance
                s.add(atts[0])
                s.commit()
            else:
                # Attribute does not exists yet
                att = TMAttribute(name, acceptance)
                s.add(att)
                s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def remove_attribute(self, name):
        log.debug("Name: " + name)
        s = None
        try:
            s = self.get_session()
            atts = s.query(TMAttribute).filter(TMAttribute.name==name).all()
            if atts is not None and len(atts) == 1:
                s.delete(atts[0])
                s.commit()
            else:
                log.error("Several attributes found. No specific deletion possible")
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def get_attribute(self, name):
        log.debug("Name: " + name)
        s = None
        att = None
        try:
            s = self.get_session()
            atts = s.query(TMAttribute).filter(TMAttribute.name==name).all()
            if atts is not None and len(atts) == 1:
                att = atts[0].toDict()
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()

        return att

    def add_update_provider(self, name, validity, correctness, factor):
        log.debug("Name: "+ name)
        log.debug("Validity: " + str(validity))
        log.debug("Correctness: " + str(correctness))
        log.debug("Factor: " + str(factor))
        s = None
        try:
            s = self.get_session()
            provs = s.query(TMProvider).filter(TMProvider.name==name).all()
            if provs is not None and len(provs) == 1:
                log.debug("Provider found")
                # Provider exists; just attributes will be updated
                provs[0].validity = validity
                provs[0].correctness = correctness
                provs[0].factor = factor

                #provs[0].validity = validity
                s.add(provs[0])
                s.commit()
            else:
                log.debug("New provider created")
                # Provider does not exists yet; create the provider
                att = TMProvider(name, validity, correctness, factor)
                s.add(att)
                s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def remove_provider(self, name):
        log.debug("Name: " + name)
        s = None
        try:
            s = self.get_session()
            prov = s.query(TMProvider).filter(TMProvider.name==name).all()
            if prov is not None and len(prov) == 1:
                s.delete(prov[0])
                s.commit()
            else:
                log.error("Several Providers found. No specific deletion possible")
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def get_provider(self, name):
        log.debug("Name: " + name)
        s = None
        prov = None
        try:
            s = self.get_session()
            provs = s.query(TMProvider).filter(TMProvider.name == name).all()
            if provs is not None and len(provs) == 1:
                log.debug("Provider found")
                prov = provs[0].toDict()
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()

        log.debug(prov)
        return prov

    def add_provider_to_attribute(self, provider, attribute, correctness=None, validity=None):
        log.debug("Provider:" + str(provider))
        log.debug("Attribute: " + str(attribute))
        log.debug("Correctness: " + str(correctness))
        log.debug("Validity: " + str(validity))
        s = None
        try:
            s = self.get_session()
            provs = s.query(TMProvider).filter(TMProvider.name == provider).all()
            atts = s.query(TMAttribute).filter(TMAttribute.name == attribute).all()
            if provs is not None and len(provs) == 1 \
                    and atts is not None and len(atts) == 1:
                # Provider and attribute exists. Relationship is created
                log.debug("Relationship created")
                already = False
                for a in provs[0].attributes:
                    if a.name == attribute:
                        already = True
                if not already:
                    provs[0].attributes.append(atts[0])
                s.add(provs[0])
                s.commit()
            else:
                # Provider or attribute does not exists, therefore no relationship is created
                log.debug("Provider or attribute does not exists. No relationship is created.")
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def remove_provider_to_attribute(self, provider, attribute):
        log.debug("Provider: " + str(provider))
        log.debug("Attribute: " + str(attribute))
        s = None
        try:
            s = self.get_session()
            provs = s.query(TMProvider).filter(TMProvider.name == provider).all()
            atts = s.query(TMAttribute).filter(TMAttribute.name == attribute).all()
            if provs is not None and len(provs) == 1 \
                    and atts is not None and len(atts) == 1:
                log.debug("Relationship removed")
                # Provider and attribute exists. Relationship is removed
                for att in provs[0].attributes:
                    if att.name == attribute:
                        provs[0].attributes.remove(att)
                s.add(provs[0])
                s.commit()
            else:
                # Provider or attribute does not exists, therefore no relationship is created
                log.debug("Provider or attribute does not exists. No relationship is created.")
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def add_provider_to_did(self, provider, did):
        log.debug("Provider: " + str(provider))
        log.debug("DID: " + did)
        s = None
        try:
            s = self.get_session()
            provs = s.query(TMProvider).filter(TMProvider.name == provider).all()
            dids = s.query(TMDID).filter(TMDID.did == did).all()
            if provs is not None and len(provs) == 1:
                # Provider must exists. DID is created on demand because a single did just refers to 1 provider
                d = None
                if dids is not None and len(dids) > 0:
                    d = dids[0]
                else:
                    d = TMDID(did)
                    s.add(d)
                provs[0].dids.append(d)
                s.add(provs[0])
                s.commit()
            else:
                # Provider does not exists, therefore no relationship is created
                log.debug("Provider or attribute does not exists. No relationship is created.")
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def remove_provider_to_did(self, provider, did):
        log.debug("Provider: " + str(provider))
        log.debug("DID: " + did)
        s = None
        try:
            s = self.get_session()
            provs = s.query(TMProvider).filter(TMProvider.name == provider).all()
            dids = s.query(TMDID).filter(TMDID.did == did).all()
            if provs is not None and len(provs) == 1 \
                    and dids is not None and len(dids) == 1:
                # Provider and DID must exists. DID is deleted.
                provs[0].dids.remove(dids[0])
                s.add(provs[0])
                s.delete(dids[0])
                s.commit()
            else:
                # Provider or did does not exists, therefore no relationship is removed
                log.debug("Provider or DID does not exists. No relationship is removed.")
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def cleanup(self):
        log.debug("Cleanup database")
        s = None
        try:
            s = self.get_session()
            provs = s.query(TMProvider).filter().all()
            atts = s.query(TMAttribute).filter().all()
            dids = s.query(TMDID).filter().all()

            for p in provs:
                s.delete(p)
            for a in atts:
                s.delete(a)
            for d in dids:
                s.delete(d)
            s.commit()

        except Exception as e:
            log.exception("Commit failed")
        finally:
            if s is not None:
                s.close()