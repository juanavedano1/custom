# C:\Users\Juan Avedano\Desktop\Facultad\Proyecto\customer_dashboard\__init__.py

from flask import Blueprint

# Definición del Blueprint (¡solo aquí!)
customer_dashboard_bp = Blueprint('customer_dashboard', __name__,
                                  template_folder='templates',
                                  static_folder='static',
                                  static_url_path='/customer_dashboard/static') # Revisa la ruta estática, '/customer_dashboard/static' es más común

# Opcional: Registra filtros o context processors que sean ESPECÍFICOS de este Blueprint
# Si los quieres para toda la app, déjalos en app.py
# from datetime import datetime # Solo si realmente vas a usarla aquí

# @customer_dashboard_bp.app_template_filter
# def today(date):
#     return date.strftime("%d-%m-%Y")

# Importa las vistas (rutas) del Blueprint. ¡Esto debe ir al final!
# Al importar .views, se ejecutan las decoraciones @customer_dashboard_bp.route
from . import views