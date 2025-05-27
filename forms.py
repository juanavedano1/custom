# C:\Users\Juan Avedano\Desktop\Facultad\Proyecto\forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, SelectField, TextAreaField # <-- Asegúrate de que SelectField y TextAreaField estén aquí
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from wtforms.widgets import ListWidget, CheckboxInput

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Contraseña Actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6, max=60)])
    confirm_new_password = PasswordField('Confirmar Nueva Contraseña', 
                                         validators=[DataRequired(), EqualTo('new_password', message='Las contraseñas no coinciden.')])
    submit = SubmitField('Cambiar Contraseña')
    
class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

# ¡NUEVO FORMULARIO PARA EDICIÓN DE USUARIOS!
class UserEditForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    # La contraseña y confirmar contraseña son OPCIONALES para la edición
    password = PasswordField('Nueva Contraseña (dejar vacío para no cambiar)', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[EqualTo('password', message='Las contraseñas deben coincidir.')])
    submit = SubmitField('Actualizar Usuario')

# ¡NUEVO FORMULARIO: Contratar Servicio!
class ContractServiceForm(FlaskForm):
    # Este campo contendrá los IDs de los servicios que el usuario seleccione
    services = SelectMultipleField(
        'Servicios Disponibles',
        coerce=int, # Asegura que los valores sean enteros (IDs de servicio)
        # widget=CheckboxSelectMultiple(), # <--- ¡CAMBIO AQUÍ TAMBIÉN!
        widget=ListWidget(prefix_label=False), # <-- Utiliza ListWidget
        option_widget=CheckboxInput(),     # <-- Y CheckboxInput para cada opción
    )
    submit = SubmitField('Contratar Servicios Seleccionados')
    # Si quisieras editar si el usuario es admin, también lo añadirías aquí:
    # is_admin = BooleanField('Es Administrador')

class ModifyServiceForm(FlaskForm):
    # Este campo 'plan' permitirá al usuario seleccionar otro "plan" para su servicio.
    # Las opciones se llenarán dinámicamente desde la base de datos en la vista de Flask.
    # 'coerce=int' es crucial para que WTForms maneje los IDs como enteros.
    plan = SelectField('Seleccionar Nuevo Plan', validators=[DataRequired()], coerce=int)
        
    # Puedes añadir más campos aquí si quieres que el usuario modifique otras cosas.
    # Por ejemplo, si un servicio tuviera una descripción editable:
    # description = TextAreaField('Descripción del Servicio', validators=[Optional(), Length(max=500)])

    submit = SubmitField('Guardar Cambios del Servicio')

class ToggleUserStatusForm(FlaskForm):
    pass 