from sqlalchemy import Column, String, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import DATABASE_URL

db_string = DATABASE_URL

Base = declarative_base()

db = create_engine(db_string)
Session = sessionmaker(db)


class AuchanProduct(Base):
    __tablename__ = 'auchan_product'

    barcode = Column(String, primary_key=True)
    name = Column(String)
    price = Column(String)
    category = Column(String)
    active = Column(Boolean)


class NovusProduct(Base):
    __tablename__ = 'novus_product'

    barcode = Column(String, primary_key=True)
    name = Column(String)
    price = Column(String)
    category = Column(String)
    active = Column(Boolean)


class MMProduct(Base):
    __tablename__ = 'mm_product'

    barcode = Column(String, primary_key=True)
    name = Column(String)
    price = Column(String)
    category = Column(String)
    active = Column(Boolean)


class Product(Base):
    __tablename__ = 'products'

    barcode = Column(String, primary_key=True)
    barcode_auchan = Column(String, ForeignKey('auchan_product.barcode'))
    barcode_novus = Column(String, ForeignKey('novus_product.barcode'))
    barcode_mm = Column(String, ForeignKey('mm_product.barcode'))
    name = Column(String)
    category = Column(String)
    volume = Column(Float)
    alcohol_volume = Column(Float)
    brend = Column(String)


Base.metadata.create_all(db)
