import json

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, PickleType, func, Table
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool
from tierion import util

Base = declarative_base()
engine = None


class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True)
    fullname = Column(String)
    password_hash = Column(String)
    salt = Column(String)
    apiKey = Column(String)
    last_token_time = Column(DateTime(timezone=True), nullable=True)

    records = relationship("Record", back_populates="owner")

    def __repr__(self):
        return "<Account(name='{}', fullname='{}', password='{}', last_token_time='{}')>".format(
            self.name, self.fullname, self.password, self.last_token_time)

    def json_describe(self):
        return json.dumps({
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "fullname": self.fullname,
            "api_key": self.apiKey
        })


class DataStore(Base):
    """
    id 	                           A unique numeric identifier for the datastore within the system.
    key 	                       A unique identifier for the datastore used when submitting from HTML forms.
    name 	                       The name of the datastore.
    groupName 	                   The name of the group of which this datastore is a member.
    redirectEnabled 	           A boolean indicating whether or not the custom redirect URL is enabled.
    redirectUrl 	               The URL a user will be redirected to when submitting data from an HTML Form.
    emailNotificationEnabled 	   A boolean indicating whether or not the email notification is enabled.
    emailNotificationAddress 	   The recipient email address.
    postDataEnabled 	           A boolean indicating whether or not the POST data URL is enabled.
    postDataUrl 	               The URL that new record data will be POSTed to when received.
    postReceiptEnabled 	           A boolean indicating whether or not the POST receipt URL is enabled.
    postReceiptUrl 	               The URL that the blockchain receipt data will be POSTed to when generated.
    timestamp 	                   The number of seconds elapsed since epoch when this Datastore was created
    """
    __tablename__ = 'datastore'

    id = Column(Integer, primary_key=True)
    key = Column(String)
    name = Column(String)
    groupName = Column(String)
    redirectEnabled = Column(Boolean)
    redirectUrl = Column(String)
    emailNotificationEnabled = Column(Boolean)
    emailNotificationAddress = Column(String)
    postDataEnabled = Column(Boolean)
    postDataUrl = Column(String)
    postReceiptEnabled = Column(Boolean)
    postReceiptUrl = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    records = relationship("Record", back_populates="datastore")

    def __repr__(self):
        return "<DataStore(id='{}', key='{}', name='{}')>".format(self.id, self.key, self.name)

    def json_describe(self):
        return json.dumps({
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "groupName": self.groupName,
            "redirectEnabled": self.redirectEnabled,
            "redirectUrl": self.redirectUrl,
            "emailNotificationEnabled": self.emailNotificationEnabled,
            "emailNotificationAddress": self.emailNotificationAddress,
            "postDataEnabled": self.postDataEnabled,
            "postDataUrl": self.postDataUrl,
            "postReceiptEnabled": self.postReceiptEnabled,
            "postReceiptUrl": self.postReceiptUrl,
            "timestamp": "{}".format(int(self.timestamp.timestamp()))
        })


class Record(Base):
    """
    id 	                        A unique identifier for the record within the system.
    accountId 	                A unique numeric identifier for the Account associated with this Record.
    datastoreId 	            A unique numeric identifier for the Datastore associated with this Record.
    status 	                    Indiciates the current state of this Record.
        - queued -                  The Record has been received, but has not yet been processed.
        - unpublished -             The Record has been processed, but not yet published to the blockchain.
        - complete -                The Record has been processed and the blockchain receipt is available.
    data 	                    A dynamic collection of key/value pairs representing the custom data received for this Record.
    json 	                    The JSON string representation of the data received for this Record.
    sha256 	                    The SHA256 hash of the JSON string representation of the data received.
    timestamp 	                The number of seconds elapsed since epoch when this Record was received.
    blockchain_receipt 	        A Blockchain Receipt object for this record, if one exists.
    insights 	                An Insights object for this record, if one exists.
    """
    __tablename__ = "record"

    id = Column(String, primary_key=True)
    accountId = Column(Integer, ForeignKey("account.id"), nullable=False)
    datastoreId = Column(Integer, ForeignKey("datastore.id"), nullable=False)
    status = Column(String, nullable=False)
    data = Column(PickleType)
    json = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    insights = Column(String)
    hashitemId = Column(Integer, ForeignKey("hashitem.id"), nullable=False)

    datastore = relationship("DataStore", back_populates="records")
    owner = relationship("Account", back_populates="records")
    hashitem = relationship("HashItem", uselist=False, back_populates="record", lazy="subquery")

    def __repr__(self):
        return "<Record(id='{}, accountId='{}', datastoreId='{}', status='{}')>".format(self.id, self.accountId,
                                                                                        self.datastoreId, self.status)

    def json_describe(self):
        return json.dumps({
            "id": self.id,
            "accountId": self.accountId,
            "datastoreId": self.datastoreId,
            "status": self.status,
            "data": self.data,
            "json": self.json,
            "sha256": self.hashitem.proof,
            "timestamp": "{}".format(int(self.timestamp.timestamp())),
            "blockchain_receipt": util.build_chainpoint_receipt(self.hashitem)
        })


item_confirmation_table = Table('item_confirmation', Base.metadata,
                                Column('item_id', Integer, ForeignKey('hashitem.id')),
                                Column('confirmation_id', Integer, ForeignKey('confirmation.id'))
                                )


class HashItem(Base):
    __tablename__ = 'hashitem'

    id = Column(Integer, primary_key=True)
    accountId = Column(Integer, ForeignKey("account.id"), nullable=False)
    sha256 = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    proof = Column(PickleType)

    confirmations = relationship("Confirmation", secondary=item_confirmation_table, back_populates="items")
    record = relationship("Record", uselist=False, back_populates="hashitem")

    def __repr__(self):
        return "<HashItem(id='{}', sha256='{}', pending='{}', timestamp='{}')>".format(
            self.id, self.sha256, len(self.confirmations) == 0, self.timestamp)

    def json_describe(self):
        return json.dumps({
            "receipt_id": self.id,
            "timestamp": "{}".format(int(self.timestamp.timestamp()))
        })


class Confirmation(Base):
    __tablename__ = 'confirmation'

    id = Column(Integer, primary_key=True)
    endpoint = Column(String, nullable=False)
    tx_id = Column(String, default=None)
    block_header = Column(String, default=None)
    merkle_root = Column(String, nullable=False)

    items = relationship("HashItem", secondary=item_confirmation_table, back_populates="confirmations")


def init(connection_string, echo):
    global engine
    if engine is None:
        engine = create_engine(connection_string, echo=echo,
                               connect_args={'check_same_thread': False},
                               poolclass=StaticPool)
        Base.metadata.create_all(engine)

    return engine


def create_session():
    global engine
    return sessionmaker(bind=engine)()
