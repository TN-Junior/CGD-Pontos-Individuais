from app import db
from datetime import datetime

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
    progressao_aplicada = db.Column(db.Boolean, default=False)
    descricao = db.Column(db.Text, nullable=True)

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