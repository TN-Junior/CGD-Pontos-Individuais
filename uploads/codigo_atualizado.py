
from flask import Flask, render_template, request, redirect, session, flash, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
from forms import UploadForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
from wtforms import StringField, IntegerField, FileField, SubmitField, SelectField, DateField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Optional
from functools import wraps
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import pyscrypt
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do aplicativo Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
app.config['SESSION_PERMANENT'] = False

# Inicialização do SQLAlchemy e migrações
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configuração de fuso horário e agendador
timezone = pytz.timezone('America/Recife')
scheduler = BackgroundScheduler(timezone=timezone)

# Constantes de limite de pontuação máxima
MAX_PONTOS_PERIODO = {
    'Instrutoria ou Coordenação de cursos promovidos pelo Município do Recife.': 10,
    'Participação em grupos, equipes, comissões e projetos especiais, no âmbito do Município do Recife, formalizados por ato oficial.': 10,
    'Exercício de cargos comissionados e funções gratificadas, ocupados, exclusivamente, no âmbito do Poder Executivo Municipal.': 15,
}

# Constantes
QUALIFICACOES = [
    "Cursos, seminários, congressos e oficinas realizados, promovidos, articulados ou admitidos pelo Município do Recife.",
    "Cursos de atualização realizados, promovidos, articulados ou admitidos pelo Município do Recife.",
    "Cursos de aperfeiçoamento realizados, promovidos, articulados ou admitidos pelo Município do Recife.",
    "Cursos de graduação e especialização realizados em instituição pública ou privada, reconhecida pelo MEC.",
    "Mestrado, doutorado e pós-doutorado realizados em instituição pública ou privada, reconhecida pelo MEC.",
    "Instrutoria ou Coordenação de cursos promovidos pelo Município do Recife.",
    "Participação em grupos, equipes, comissões e projetos especiais, no âmbito do Município do Recife, formalizados por ato oficial.",
    "Exercício de cargos comissionados e funções gratificadas, ocupados, exclusivamente, no âmbito do Poder Executivo Municipal."
]

# Modelos
class Curso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    pontos = db.Column(db.Integer, default=0)

class Certificado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(50), unique=True, nullable=False)
    qualificacao = db.Column(db.String(255), nullable=False)
    periodo_de = db.Column(db.Date, nullable=True)
    periodo_ate = db.Column(db.Date, nullable=True)
    carga_horaria = db.Column(db.Integer, nullable=True)
    quantidade = db.Column(db.Integer, nullable=True)
    pontos = db.Column(db.Integer, nullable=False)
    horas_excedentes = db.Column(db.Integer, nullable=False, default=0)
    ano_conclusao = db.Column(db.Integer, nullable=True)
    ato_normativo = db.Column(db.String(100), nullable=True)
    tempo = db.Column(db.Integer, nullable=True)
    filename = db.Column(db.String(200), nullable=False)
    aprovado = db.Column(db.Boolean, default=False)
    recusado = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'))
    curso = db.relationship('Curso', backref=db.backref('certificados', lazy=True))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario', backref=db.backref('certificados', lazy=True))
    progressao = db.Column(db.Integer, default=0)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(80), unique=True, nullable=False)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pontuacao = db.Column(db.Integer, default=0)
    senha = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')

    def __repr__(self):
        return f'<Usuario {self.nome}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(150), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    recipient = db.Column(db.String(150), nullable=False)

# Formulários
class UploadForm(FlaskForm):
    qualificacao = SelectField(
        'Qualificação',
        choices=[('', 'Selecione')] + [(qualificacao, qualificacao) for qualificacao in QUALIFICACOES],
        validators=[DataRequired(message="Selecione uma qualificação.")]
    )
    periodo_de = DateField('Período (de)', validators=[Optional()])
    periodo_ate = DateField('Período (até)', validators=[Optional()])
    horas = IntegerField('Horas', validators=[Optional()])
    quantidade = IntegerField('Quantidade', validators=[Optional()])
    ano_conclusao = IntegerField('Ano de Conclusão', validators=[Optional()])
    ato_normativo = StringField('Ato Normativo', validators=[Optional()])
    tempo = IntegerField('Tempo (anos/meses)', validators=[Optional()])
    certificate = FileField('Certificado', validators=[DataRequired(message="Certificado é obrigatório.")])
    submit = SubmitField('Enviar')
