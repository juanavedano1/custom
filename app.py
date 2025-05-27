# C:\Users\Juan Avedano\Desktop\Facultad\Proyecto\app.py

import os
from flask import Flask, render_template, redirect, url_for, flash, request, Blueprint, current_app
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
from forms import LoginForm, RegistrationForm, UserEditForm, ContractServiceForm, ToggleUserStatusForm
# from config import Config # <-- Mantenla comentada si no tienes un config.py con tu URL de DB
from functools import wraps
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
#from flask_wtf import FlaskForm
#from wtforms import SubmitField
# Importar el blueprint del customer_dashboard
from customer_dashboard.views import customer_dashboard_bp

# === IMPORTAR la instancia 'db' declarada en models.py ===
from models import db, User, Service, Complaint, user_services_association # <-- Importa 'db' también, junto con los modelos

print("=== DEBUG: app.py ha sido recargado y ejecutado ===")
# === INSTANCIA DE LA APP Y CONFIGURACIÓN ===
app = Flask(__name__)

csrf = CSRFProtect(app)
# --- Configuración de la base de datos MySQL ---
app.config["SECRET_KEY"] = "PirataCordobesInstaMegaNashey2025"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:juancho16@localhost:3306/customer_portal'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SIMULATION_MODE'] = False # Cambia a True para simulación sin DB real

# === INSTANCIAS DE EXTENSIÓN INICIALIZADAS CON LA APP YA CONFIGURADA ===
db.init_app(app) # <-- Aquí inicializamos la 'db' que los modelos están usando.

bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)
migrate = Migrate(app, db)

# Define un User mock para el modo simulación si no hay DB real
class MockUser(UserMixin):
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True
    @property
    def is_authenticated(self):
        return True
    @property
    def is_anonymous(self):
        return False

    def check_password(self, password):
        mock_passwords = {
            'admin': 'admin123',
            'cliente': 'cliente123',
            'test': 'test123'
        }
        return mock_passwords.get(self.username) == password

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@login_manager.user_loader
def load_user(user_id):
    if app.config['SIMULATION_MODE']:
        mock_users_data = {
            1: {'username': 'admin', 'email': 'admin@example.com', 'is_admin': True},
            2: {'username': 'cliente', 'email': 'cliente@example.com', 'is_admin': False},
            3: {'username': 'test', 'email': 'test@example.com', 'is_admin': False},
        }
        user_data = mock_users_data.get(int(user_id))
        if user_data:
            return MockUser(int(user_id), user_data['username'], user_data['email'], user_data['is_admin'])
        return None
    else:
          # Solo cargar si el usuario existe y está activo
        user = User.query.get(int(user_id))
        if user and user.is_active: # <-- Verificar si el usuario está activo
            return user
        return None # No cargar el usuario si no existe o no está activo

# --- Decoradores personalizados ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acceso denegado. Solo administradores pueden acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rutas de Autenticación y Registro ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer_dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user_found = None
        if app.config['SIMULATION_MODE']:
            mock_users_data = {
                'admin': {'id': 1, 'username': 'admin', 'email': 'admin@example.com', 'is_admin': True, 'password': 'admin123'},
                'cliente': {'id': 2, 'username': 'cliente', 'email': 'cliente@example.com', 'is_admin': False, 'password': 'cliente123'},
                'test': {'id': 3, 'username': 'test', 'email': 'test@example.com', 'is_admin': False, 'password': 'test123'},
            }
            user_data = mock_users_data.get(username)
            if user_data:
                if user_data['password'] == password:
                    user_found = MockUser(user_data['id'], user_data['username'], user_data['email'], user_data['is_admin'])
        else:
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                user_found = user

        if user_found:
            if user_found.is_active:
                login_user(user_found, remember=form.remember_me.data)
                flash('Inicio de sesión exitoso!', 'success')
                if user_found.is_admin:
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('customer_dashboard.index'))
            else:
                flash('Tu cuenta ha sido desactivada. Por favor, contacta al administrador.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer_dashboard.index'))

    if app.config['SIMULATION_MODE']:
        flash('El registro de nuevos usuarios está deshabilitado en modo de simulación. Por favor, usa las cuentas predefinidas.', 'info')
        return redirect(url_for('login'))
    else:
        form = RegistrationForm()
        if form.validate_on_submit():
            existing_user = User.query.filter_by(username=form.username.data).first()
            existing_email = User.query.filter_by(email=form.email.data).first()

            if existing_user:
                flash('Ese nombre de usuario ya existe. Por favor, elige otro.', 'danger')
            elif existing_email:
                flash('Ese email ya está registrado por otro usuario. Por favor, usa otro.', 'danger')
            else:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                user = User(username=form.username.data, email=form.email.data, password=hashed_password, is_admin=False, is_active = True)
                db.session.add(user)
                db.session.commit()
                flash('Tu cuenta ha sido creada con éxito! Por favor, inicia sesión.', 'success')
                return redirect(url_for('login'))
        return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

# --- Rutas de la Raíz ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer_dashboard.index'))
    return redirect(url_for('login'))

# --- Registro de Blueprints ---
app.register_blueprint(customer_dashboard_bp, url_prefix='/customer')

admin_bp = Blueprint('admin', __name__, template_folder='templates/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin_dashboard.html', active_tab='overview')

@admin_bp.route('/manage_users')
@login_required
@admin_required
def manage_users():
    if current_app.config['SIMULATION_MODE']:
        users = [
            {'id': 1, 'username': 'admin', 'email': 'admin@example.com', 'is_admin': True, 'is_active': True},
            {'id': 2, 'username': 'cliente', 'email': 'cliente@example.com', 'is_admin': False, 'is_active': True},
            {'id': 3, 'username': 'test', 'email': 'test@example.com', 'is_admin': False, 'is_active': False},
        ]
        toggle_form = ToggleUserStatusForm()
        return render_template('admin_user.html', users=users, active_tab='users', toggle_form=toggle_form)
    else:
        users = User.query.all()
        toggle_form = ToggleUserStatusForm()
        return render_template('admin_user.html', users=users, active_tab='users', toggle_form=toggle_form)

@admin_bp.route('/user_detail/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    if app.config['SIMULATION_MODE']:
        mock_users_data = {
            1: {'id': 1, 'username': 'admin', 'email': 'admin@example.com', 'is_admin': True, 'registration_date': '2023-01-01 10:00:00', 'last_login': '2025-05-23 18:30:00', 'is_active': True},
            2: {'id': 2, 'username': 'cliente', 'email': 'cliente@example.com', 'is_admin': False, 'registration_date': '2023-02-15 12:00:00', 'last_login': '2025-05-23 18:00:00', 'is_active': True},
            3: {'id': 3, 'username': 'test', 'email': 'test@example.com', 'is_admin': False, 'registration_date': '2023-03-20 09:00:00', 'last_login': '2025-05-23 17:00:00', 'is_active': True},
        }
        user_data_to_display = mock_users_data.get(user_id, {'id': user_id, 'username': 'Usuario Desconocido', 'email': 'unknown@example.com', 'is_admin': False, 'is_active': False})

        user_services_to_display = []
        if user_id == 2:
            user_services_to_display = [
                {'id': 101, 'name': 'Internet Fibra Óptica 300Mbps', 'type': 'Internet', 'price': 35000.00},
                {'id': 103, 'name': 'TV Cable Premium', 'type': 'TV', 'price': 25000.00},
            ]
        else:
             user_services_to_display = []

    else:
        user_data_to_display = User.query.get_or_404(user_id)
        user_services_to_display = user_data_to_display.services_contracted.all()

    toggle_form = ToggleUserStatusForm()
    return render_template('admin_detail.html', user=user_data_to_display, user_services=user_services_to_display, active_tab='users',**{'toggle_form': toggle_form})

@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    if app.config['SIMULATION_MODE']:
        flash(f'Simulando edición de usuario. (No se guardó realmente)', 'info')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    else:
        user = User.query.get_or_404(user_id)
        form = UserEditForm()

        if form.validate_on_submit():
            existing_user_by_username = User.query.filter(User.username == form.username.data, User.id != user_id).first()
            existing_user_by_email = User.query.filter(User.email == form.email.data, User.id != user_id).first()

            if existing_user_by_username:
                flash('Ese nombre de usuario ya existe para otro usuario. Por favor, elige otro.', 'danger')
            elif existing_user_by_email:
                flash('Ese email ya está registrado por otro usuario. Por favor, usa otro.', 'danger')
            else:
                user.username = form.username.data
                user.email = form.email.data
                if form.password.data:
                    user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

                if 'is_active' in form and current_user.id != user_id:
                     user.is_active = form.is_active.data
                if 'is_admin' in form:
                    user.is_admin = form.is_admin.data

                db.session.commit()
                flash('Usuario actualizado exitosamente!', 'success')
                return redirect(url_for('admin.user_detail', user_id=user.id))
        elif request.method == 'GET':
            form.username.data = user.username
            form.email.data = user.email
            if 'is_admin' in form:
                 form.is_admin.data = user.is_admin
            if 'is_active' in form:
                 form.is_active.data = user.is_active

        user_services_to_display = []
        return render_template('admin_edit_user.html', user=user, user_services=user_services_to_display, active_tab='users', form=form)

@admin_bp.route('/toggle_service_status/<int:service_id>', methods=['POST'])
@login_required
@admin_required
def toggle_service_status(service_id):
    if app.config['SIMULATION_MODE']:
        flash(f'Simulando cambio de estado para el servicio {service_id}. (No se guardó realmente)', 'info')
        return redirect(url_for('admin.manage_users'))
    else:
        service_item = Service.query.get_or_404(service_id)
        flash(f'Funcionalidad de cambio de estado de servicio NO IMPLEMENTADA en DB real aún.', 'warning')
        return redirect(url_for('admin.manage_users'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if app.config['SIMULATION_MODE']:
        flash(f'Simulando eliminación del usuario {user_id}. (No se eliminó realmente)', 'danger')
        return redirect(url_for('admin.manage_users'))
    else:
        user_to_delete = User.query.get_or_404(user_id)
        Complaint.query.filter_by(user_id=user_id).delete()
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuario {user_to_delete.username} eliminado permanentemente.', 'success')
        return redirect(url_for('admin.manage_users'))

@admin_bp.route('/toggle_user_active_status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_active_status(user_id):
    if app.config['SIMULATION_MODE']:
        flash(f'Simulando cambio de estado de actividad para el usuario {user_id}. (No se guardó realmente)', 'info')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    else:
        user = User.query.get_or_404(user_id)
        form = ToggleUserStatusForm()
        if form.validate_on_submit():
            if user.is_admin:
                flash('No se puede desactivar la cuenta de un administrador.', 'danger')
                return redirect(url_for('admin.user_detail', user_id=user_id))

            user.is_active = not user.is_active
            db.session.commit()
            flash(f'El usuario "{user.username}" ha sido {"activado" if user.is_active else "desactivado"} exitosamente.', 'success')
            return redirect(url_for('admin.user_detail', user_id=user.id))
        else:
            flash('Error de seguridad: Token CSRF inválido o ausente.', 'danger')
            return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    flash('Esta es la página de configuración del administrador (contenido estático).', 'info')
    return render_template('admin_dashboard.html', admin_section_content="<h2><i class='bi bi-gear'></i> Configuración del Sistema</h2><p>Aquí irían las opciones de configuración global del panel de administración.</p>", active_tab='settings')

app.register_blueprint(admin_bp, url_prefix='/admin')

if __name__ == '__main__':
    with app.app_context():
        try:
            # db.create_all() # Ya comentada, ¡no la descomentes!
            print("Tablas de la base de datos creadas/actualizadas.")

            # Lógica para crear el usuario admin si no existe
            if not User.query.filter_by(username='admin').first():
                hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
                admin_user = User(username='admin', email='admin@example.com', password=hashed_password, is_admin=True, is_active=True)
                db.session.add(admin_user)
                db.session.commit()
                print("Usuario admin creado automáticamente.")
            else:
                print("El usuario admin ya existe, no se creó.")

            # Lógica para crear servicios de ejemplo si no existen
            if not Service.query.first():
                service1 = Service(name="Internet Fibra Óptica 300Mbps", description="Conexión de alta velocidad para hogar y teletrabajo.", price=35000.00)
                service2 = Service(name="Telefonía Fija Ilimitada", description="Llamadas ilimitadas a números fijos nacionales.", price=15000.00)
                service3 = Service(name="TV Cable Premium", description="Paquete con más de 100 canales HD, incluye deportes y películas.", price=25000.00)

                db.session.add_all([service1, service2, service3])
                db.session.commit()
                print("Servicios de ejemplo creados automáticamente.")
            else:
                print("Los servicios ya existen, no se crearon nuevos.")

        except Exception as e:
            print(f"Error en el contexto de la aplicación durante la inicialización: {e}")
            print("Asegúrate de que la base de datos está accesible y las tablas existen.")

    app.run(debug=True)