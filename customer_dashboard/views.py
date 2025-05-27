# C:\Users\Juan Avedano\Desktop\Facultad\Proyecto\customer_dashboard\views.py

from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from datetime import datetime

from models import db, User, Service
from forms import ContractServiceForm, ModifyServiceForm, ChangePasswordForm


# Define tu Blueprint. Ajusta el template_folder para que apunte a 'templates/customer_dashboard'
# La ruta es relativa a la ubicación del app.py
customer_dashboard_bp = Blueprint('customer_dashboard', __name__, template_folder='../templates/customer_dashboard') # <-- CAMBIO CLAVE AQUI
# NOTA: '../../' significa que sube dos niveles desde views.py (customer_dashboard -> Proyecto) y luego entra a templates/customer_dashboard

@customer_dashboard_bp.route('/')
@customer_dashboard_bp.route('/index')
@login_required
def index():
    user_services = []
    if not current_app.config.get('SIMULATION_MODE', False):
        if hasattr(current_user, 'services_contracted'):
            user_services = current_user.services_contracted.all()

    # CAMBIO DE NOMBRE DE LA PLANTILLA:
    return render_template('dashboard_index.html', user_services=user_services, active_tab='dashboard')


# --- RUTA: Ver Perfil/Datos del Usuario ---
@customer_dashboard_bp.route('/profile')
@login_required
def view_profile():
    user_data = current_user
    user_services = []

    if current_app.config.get('SIMULATION_MODE', False):
        # Mock de datos para la vista de perfil en simulación
        if user_data.id == '2':
            user_data = type('User', (object,), {
                'id': '2', 'username': 'cliente', 'email': 'cliente@example.com',
                'registration_date': datetime(2023, 2, 15, 12, 0, 0),
                'last_login': datetime.now(),
                'is_active': True,
                'is_admin': False,
                'get_id': lambda: '2', 'is_authenticated': True, 'is_active': True, 'is_anonymous': False
            })()
            user_services = [
                {'name': 'Internet Fibra Óptica', 'type': 'Internet', 'price': 35000.00, 'description': 'Conexión de alta velocidad'},
                {'name': 'Telefonía Móvil', 'type': 'Móvil', 'price': 20000.00, 'description': 'Plan con 10GB de datos'},
            ]
        elif user_data.id == '1':
            user_data = type('User', (object,), {
                'id': '1', 'username': 'admin', 'email': 'admin@example.com',
                'registration_date': datetime(2023, 1, 1, 10, 0, 0),
                'last_login': datetime.now(),
                'is_active': True,
                'is_admin': True,
                'get_id': lambda: '1', 'is_authenticated': True, 'is_active': True, 'is_anonymous': False
            })()
            user_services = []

    else:
        if hasattr(current_user, 'services_contracted'):
            user_services = current_user.services_contracted.all()

    # La plantilla 'profile.html' está directamente dentro de 'templates/customer_dashboard'
    return render_template('profile.html', user=user_data, user_services=user_services, active_tab='profile')


# --- RUTA: Cambiar Contraseña ---
@customer_dashboard_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_app.config.get('SIMULATION_MODE', False):
            flash('El cambio de contraseña no está disponible en modo simulación.', 'warning')
            return redirect(url_for('customer_dashboard.change_password'))
        else:
            # Esta línea ya no dará AttributeError una vez que models.py esté actualizado
            if not current_user.check_password(form.old_password.data):
                flash('La contraseña actual es incorrecta.', 'danger')
                return render_template('change_password.html', form=form, active_tab='change_password')

            # Esta línea ya no dará AttributeError una vez que models.py esté actualizado
            current_user.set_password(form.new_password.data) # Usa el método para hashear y guardar
            db.session.commit()
            flash('Tu contraseña ha sido actualizada exitosamente.', 'success')
            return redirect(url_for('customer_dashboard.view_profile'))
    return render_template('change_password.html', form=form, active_tab='change_password')


# --- RUTA PARA CONTRATAR SERVICIOS ---
@customer_dashboard_bp.route('/contract_service', methods=['GET', 'POST'])
@login_required
def customer_contract_service():
    form = ContractServiceForm()

    available_services = Service.query.all()
    form.services.choices = [(service.id, f"{service.name} (${service.price:,.2f})") for service in available_services]

    if form.validate_on_submit():
        selected_service_ids = form.services.data

        for service_id in selected_service_ids:
            service = Service.query.get(service_id)
            if service and service not in current_user.services_contracted:
                current_user.services_contracted.append(service)

        db.session.commit()
        flash('Servicios contratados exitosamente!', 'success')
        return redirect(url_for('customer_dashboard.index'))

    # La plantilla 'contract_service.html' está directamente dentro de 'templates/customer_dashboard'
    return render_template('contract_service.html', form=form, active_tab='contract_service')

# --- RUTA: Gestión de Servicios (donde se listan para modificar) ---
@customer_dashboard_bp.route('/service_management')
@login_required
def service_management():
    user_services = current_user.services_contracted.all()
    # La plantilla 'service_management.html' está directamente dentro de 'templates/customer_dashboard'
    return render_template('service_management.html', user_services=user_services, active_tab='service_management')


# --- RUTA: Modificar un Servicio Específico ---
@customer_dashboard_bp.route('/services/modify/<int:service_id>', methods=['GET', 'POST'])
@login_required
def modify_service(service_id):
    service_to_modify = Service.query.get_or_404(service_id)

    if service_to_modify not in current_user.services_contracted:
        flash('No tienes permiso para modificar este servicio.', 'danger')
        return redirect(url_for('customer_dashboard.service_management'))

    form = ModifyServiceForm()

    available_plans = [
        (service.id, f"{service.name} (${service.price:,.2f})")
        for service in Service.query.filter_by(type=service_to_modify.type).all()
    ]
    form.plan.choices = available_plans

    if form.validate_on_submit():
        new_plan_service_id = form.plan.data
        new_plan_service = Service.query.get(new_plan_service_id)

        if new_plan_service:
            if new_plan_service.id != service_to_modify.id:
                current_user.services_contracted.remove(service_to_modify)
                current_user.services_contracted.append(new_plan_service)

                db.session.commit()
                flash(f'Tu servicio "{service_to_modify.name}" ha sido actualizado a "{new_plan_service.name}" exitosamente!', 'success')
            else:
                flash('No se realizaron cambios porque el plan seleccionado es el mismo que ya tienes.', 'info')
        else:
            flash('El plan de servicio seleccionado no es válido.', 'danger')

        return redirect(url_for('customer_dashboard.service_management'))

    elif request.method == 'GET':
        form.plan.data = service_to_modify.id

    # La plantilla 'modify_service.html' está directamente dentro de 'templates/customer_dashboard'
    return render_template('modify_service.html',
                            form=form,
                            service=service_to_modify,
                            active_tab='service_management')


@customer_dashboard_bp.route('/services/unsubscribe/<int:service_id>', methods=['POST'])
@login_required
def unsubscribe_service(service_id):
    service_to_unsubscribe = Service.query.get_or_404(service_id)

    if service_to_unsubscribe not in current_user.services_contracted:
        flash('No tienes permiso para dar de baja este servicio o no está contratado por ti.', 'danger')
        return redirect(url_for('customer_dashboard.service_management'))

    try:
        current_user.services_contracted.remove(service_to_unsubscribe)
        db.session.commit()

        flash(f'El servicio "{service_to_unsubscribe.name}" ha sido dado de baja exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al intentar dar de baja el servicio: {e}', 'danger')

    return redirect(url_for('customer_dashboard.service_management'))