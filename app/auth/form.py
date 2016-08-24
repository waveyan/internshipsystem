from flask.ext.wtf import Form
from wtforms import StringField, SubmitField,PasswordField,BooleanField
from wtforms.validators import Required


class LoginForm(Form):
    ID= StringField('ID', validators=[Required()])
    password= PasswordField('password',validators=[Required()])
    remember_me=BooleanField('Keep me logged in')
    submit = SubmitField('Log In')
