from base.database import SSIXASQLBaseDBBase

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Table, ForeignKey, UniqueConstraint, Float

import logging
log = logging.getLogger(__name__)

class TMAttribute(SSIXASQLBaseDBBase):
    __tablename__ = 'tm_attribute'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    acceptance = Column(Float)

    def __init__(self, name, acceptance=0.0):
        self.name = name
        self.acceptance = acceptance

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def toDict(self):
        return {"name": self.name, "acceptance": self.acceptance}

    @staticmethod
    def fromDict(dic):
        return TMAttribute(dic["name"],dic['acceptance'])

providerdeliversattribute_association = Table(
    'tm_providerdeliversattribute', SSIXASQLBaseDBBase.metadata,
    Column('provider_id', Integer, ForeignKey('tm_provider.id')),
    Column('attribute_id', Integer, ForeignKey('tm_attribute.id')),
    Column('correctness', Float),
    Column('validity', Float),
    UniqueConstraint('provider_id','attribute_id',name='tm_provider_attribute_uc')
)

providertodid_association = Table(
    'tm_providertodid', SSIXASQLBaseDBBase.metadata,
    Column('provider_id', Integer, ForeignKey('tm_provider.id')),
    Column('did_id', Integer, ForeignKey('tm_did.id')),
    UniqueConstraint('provider_id','did_id',name='tm_provider_did_uc')
)

class TMProvider(SSIXASQLBaseDBBase):
    __tablename__ = 'tm_provider'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    correctness = Column(Float)
    validity = Column(Float)
    factor = Column(Float)
    attributes = relationship("TMAttribute", secondary=providerdeliversattribute_association)
    dids = relationship("TMDID", secondary=providertodid_association)

    def __init__(self, name, correctness=0.0, validity=0.0, factor=0.0):
        self.name = name
        self.correctness = correctness
        self.validity = validity
        self.factor = factor

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def toDict(self):
        at = []
        for a in self.attributes:
            at.append(a.toDict())
        di = []
        for d in self.dids:
            di.append(d.did)

        return {"name": self.name,
                "correctness": str(self.correctness),
                "validity": str(self.validity),
                "factor": str(self.factor),
                "attributes": at,
                "dids": di}

    @staticmethod
    def fromDict(dic):
        return TMProvider(dic['name'],dic['correctness'], dic['validity'], dic['factor'])

class TMDID(SSIXASQLBaseDBBase):
    __tablename__ = 'tm_did'

    id = Column(Integer, primary_key=True)
    did = Column(String, unique=True)

    def __init__(self, did):
        self.did = did

    def __eq__(self, other):
        return self.did == other.did

    def __str__(self):
        return self.did

    def __hash__(self):
        return hash(self.did)