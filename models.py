# C:\Users\Juan Avedano\Desktop\Facultad\Proyecto\models.py

from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey # <-- ¡Importa Table, Column, Integer, ForeignKey!

db = SQLAlchemy()

# Definición de la tabla de asociación
# Esta tabla conectará usuarios con servicios que han contratado
user_services_association = db.Table(
    'user_services_association', # Nombre de la tabla de asociación en la DB
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('service.id'), primary_key=True),
    # Puedes añadir otras columnas si necesitas almacenar datos sobre la suscripción
    # Por ejemplo: db.Column('contract_date', db.DateTime, default=db.func.current_timestamp())
    # O un estado de la suscripción (activo/inactivo): db.Column('status', db.String(50), default='activo')
)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    complaints = db.relationship('Complaint', backref='complainant', lazy=True)

    # Relación muchos-a-muchos con Service a través de la tabla de asociación
    # backref='users_who_contracted' permite acceder a los usuarios desde un servicio
    # lazy='dynamic' es útil para consultas encadenadas (ej. user.services.filter_by(...))
    services_contracted = db.relationship(
        'Service',
        secondary=user_services_association,
        backref=db.backref('users_who_contracted', lazy='dynamic'),
        lazy='dynamic'
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', 'Admin: {self.is_admin}')"

class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False, default='General')
    complaints = db.relationship('Complaint', backref='service_offered', lazy=True)
    # Ya no necesitas una relación directa con User aquí, la tabla de asociación lo maneja
    # La 'backref' en User ya crea la relación inversa

    def __repr__(self):
        return f"Service('{self.name}', '{self.type}', '{self.price}')"

class Complaint(db.Model):
    __tablename__ = 'complaint'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pendiente')
    date_created = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    def __repr__(self):
        return f"Complaint('{self.subject}', '{self.status}')"