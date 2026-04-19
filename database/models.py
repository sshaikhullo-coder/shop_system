from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base ()


class UserRole ( enum.Enum ):
    ADMIN = "admin"
    CASHIER = "cashier"
    MANAGER = "manager"


class PaymentType ( enum.Enum ):
    CASH = "cash"
    CARD = "card"
    CREDIT = "credit"


class UnitType ( enum.Enum ):
    PIECE = "шт"
    KG = "кг"
    GRAM = "г"
    LITER = "л"


class User ( Base ):
    __tablename__ = 'users'
    id = Column ( Integer, primary_key=True )
    username = Column ( String ( 50 ), unique=True, nullable=False )
    password = Column ( String ( 255 ), nullable=False )
    full_name = Column ( String ( 100 ) )
    role = Column ( Enum ( UserRole ), default=UserRole.CASHIER )
    is_active = Column ( Boolean, default=True )
    created_at = Column ( DateTime, default=datetime.now )
    last_login = Column ( DateTime )

    sales = relationship ( "Sale", back_populates="user" )


class Category ( Base ):
    __tablename__ = 'categories'
    id = Column ( Integer, primary_key=True )
    name = Column ( String ( 50 ), unique=True, nullable=False )
    description = Column ( String ( 200 ) )

    products = relationship ( "Product", back_populates="category" )


class Product ( Base ):
    __tablename__ = 'products'
    id = Column ( Integer, primary_key=True )
    barcode = Column ( String ( 50 ), unique=True, nullable=True )
    name = Column ( String ( 100 ), nullable=False )
    category_id = Column ( Integer, ForeignKey ( 'categories.id' ) )
    price = Column ( Float, nullable=False )
    cost_price = Column ( Float, default=0.0 )
    unit_type = Column ( Enum ( UnitType ), default=UnitType.PIECE )
    stock = Column ( Float, default=0.0 )
    min_stock = Column ( Float, default=5.0 )
    is_active = Column ( Boolean, default=True )
    created_at = Column ( DateTime, default=datetime.now )
    archived_at = Column ( DateTime, nullable=True )
    expiry_date = Column ( DateTime, nullable=True )  # Мөөнөтү өткөн товар үчүн

    category = relationship ( "Category", back_populates="products" )
    sale_items = relationship ( "SaleItem", back_populates="product", cascade="all, delete-orphan" )
    expired_items = relationship ( "ExpiredProduct", back_populates="product", cascade="all, delete-orphan" )
    returns = relationship ( "ReturnedProduct", back_populates="product", cascade="all, delete-orphan" )
    profits = relationship ( "ProfitLog", back_populates="product", cascade="all, delete-orphan" )


class Sale ( Base ):
    __tablename__ = 'sales'
    id = Column ( Integer, primary_key=True )
    sale_number = Column ( String ( 50 ), unique=True, nullable=False )
    user_id = Column ( Integer, ForeignKey ( 'users.id' ) )
    customer_id = Column ( Integer, ForeignKey ( 'customers.id' ), nullable=True )
    payment_type = Column ( Enum ( PaymentType ), nullable=False )
    total_amount = Column ( Float, nullable=False )
    paid_amount = Column ( Float, nullable=False )
    change_amount = Column ( Float, default=0.0 )
    notes = Column ( String ( 200 ) )
    created_at = Column ( DateTime, default=datetime.now )

    user = relationship ( "User", back_populates="sales" )
    customer = relationship ( "Customer", back_populates="sales" )
    items = relationship ( "SaleItem", back_populates="sale", cascade="all, delete-orphan" )
    credit = relationship ( "Credit", back_populates="sale", uselist=False )
    returns = relationship ( "ReturnedProduct", back_populates="sale", cascade="all, delete-orphan" )
    profits = relationship ( "ProfitLog", back_populates="sale", cascade="all, delete-orphan" )


class SaleItem ( Base ):
    __tablename__ = 'sale_items'
    id = Column ( Integer, primary_key=True )
    sale_id = Column ( Integer, ForeignKey ( 'sales.id' ) )
    product_id = Column ( Integer, ForeignKey ( 'products.id' ) )
    quantity = Column ( Float, nullable=False )
    price = Column ( Float, nullable=False )
    total = Column ( Float, nullable=False )

    sale = relationship ( "Sale", back_populates="items" )
    product = relationship ( "Product", back_populates="sale_items" )


class Customer ( Base ):
    __tablename__ = 'customers'
    id = Column ( Integer, primary_key=True )
    name = Column ( String ( 100 ), nullable=False )
    phone = Column ( String ( 20 ) )
    address = Column ( String ( 200 ) )
    created_at = Column ( DateTime, default=datetime.now )

    sales = relationship ( "Sale", back_populates="customer" )
    credits = relationship ( "Credit", back_populates="customer" )


class Credit ( Base ):
    __tablename__ = 'credits'
    id = Column ( Integer, primary_key=True )
    customer_id = Column ( Integer, ForeignKey ( 'customers.id' ) )
    sale_id = Column ( Integer, ForeignKey ( 'sales.id' ) )
    amount = Column ( Float, nullable=False )
    paid_amount = Column ( Float, default=0.0 )
    status = Column ( String ( 20 ), default='pending' )
    due_date = Column ( DateTime )
    created_at = Column ( DateTime, default=datetime.now )

    customer = relationship ( "Customer", back_populates="credits" )
    sale = relationship ( "Sale", back_populates="credit" )


class ExpiredProduct ( Base ):
    __tablename__ = 'expired_products'
    id = Column ( Integer, primary_key=True )
    product_id = Column ( Integer, ForeignKey ( 'products.id' ) )
    product_name = Column ( String ( 100 ) )
    barcode = Column ( String ( 50 ) )
    expiry_date = Column ( DateTime, nullable=False )
    quantity = Column ( Float, default=0.0 )
    notes = Column ( String ( 200 ) )
    created_at = Column ( DateTime, default=datetime.now )
    status = Column ( String ( 20 ), default='active' )

    product = relationship ( "Product", back_populates="expired_items" )


class ReturnedProduct ( Base ):
    __tablename__ = 'returned_products'
    id = Column ( Integer, primary_key=True )
    sale_id = Column ( Integer, ForeignKey ( 'sales.id' ) )
    product_id = Column ( Integer, ForeignKey ( 'products.id' ) )
    product_name = Column ( String ( 100 ) )
    barcode = Column ( String ( 50 ) )
    quantity = Column ( Float, nullable=False )
    return_price = Column ( Float, nullable=False )
    reason = Column ( String ( 200 ) )
    return_date = Column ( DateTime, default=datetime.now )
    status = Column ( String ( 20 ), default='pending' )

    sale = relationship ( "Sale", back_populates="returns" )
    product = relationship ( "Product", back_populates="returns" )


class ProfitLog ( Base ):
    __tablename__ = 'profit_logs'
    id = Column ( Integer, primary_key=True )
    product_id = Column ( Integer, ForeignKey ( 'products.id' ) )
    product_name = Column ( String ( 100 ) )
    sale_id = Column ( Integer, ForeignKey ( 'sales.id' ) )
    quantity = Column ( Float, nullable=False )
    selling_price = Column ( Float, nullable=False )
    cost_price = Column ( Float, nullable=False )
    profit = Column ( Float, nullable=False )
    profit_percent = Column ( Float, default=0.0 )
    created_at = Column ( DateTime, default=datetime.now )

    product = relationship ( "Product", back_populates="profits" )
    sale = relationship ( "Sale", back_populates="profits" )


class BackupLog ( Base ):
    __tablename__ = 'backup_logs'
    id = Column ( Integer, primary_key=True )
    backup_date = Column ( DateTime, default=datetime.now )
    file_path = Column ( String ( 255 ) )
    status = Column ( String ( 20 ) )
    notes = Column ( String ( 500 ) )