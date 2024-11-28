from functools import wraps
from flask import session, redirect, url_for, flash
from app import db
from models import Usuario, Certificado
from datetime import datetime
import pyscrypt, os
from config import QUALIFICACOES, MAX_PONTOS_PERIODO

# Funções utilitárias
def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario_id = session.get('usuario_logado')
        usuario = db.session.get(Usuario, usuario_id)
        if usuario and usuario.role == 'admin':
            return f(*args, **kwargs)
        else:
            flash('Acesso negado. Área restrita a administradores.')
            return redirect(url_for('index'))
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_logado' not in session:
            flash('Você precisa estar logado para acessar essa página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

def calcular_pontos(certificado_data):
    """
    Calcula os pontos e horas excedentes com base na qualificação e carga horária.
    Retorna os pontos calculados e as horas excedentes para salvar no banco.
    """
    qualificacao = certificado_data['qualificacao']
    horas = certificado_data.get('horas', 0)  # Define 0 se horas for None
    tempo = certificado_data.get('tempo', 0)
    pontos = 0
    horas_excedentes = 0

    # Calcula os pontos e horas excedentes com base na qualificação
    if qualificacao == 'Cursos, seminários, congressos e oficinas realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
        pontos = (horas // 20) * 2
        horas_excedentes = horas % 20
    elif qualificacao == 'Cursos de atualização realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
        if horas >= 40:
            pontos = 5
            horas_excedentes = horas - 40
    elif qualificacao == 'Cursos de aperfeiçoamento realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
        if horas >= 180:
            pontos = 10
            horas_excedentes = horas - 180
    elif qualificacao == 'Cursos de graduação e especialização realizados em instituição pública ou privada, reconhecida pelo MEC.':
        if horas >= 360:
            pontos = 20
            horas_excedentes = horas - 360
    elif qualificacao == 'Mestrado, doutorado e pós-doutorado realizados em instituição pública ou privada, reconhecida pelo MEC.':
        pontos = 30
        horas_excedentes = 0
    elif qualificacao == 'Instrutoria ou Coordenação de cursos promovidos pelo Município do Recife.':
        if horas >= 8:
            pontos = (horas // 8) * 2
            if pontos > MAX_PONTOS_PERIODO[qualificacao]:  # Limite máximo
                pontos = MAX_PONTOS_PERIODO[qualificacao]
            horas_excedentes = horas % 8
        else:
            horas_excedentes = horas  # Armazena horas menores que 8 diretamente como horas excedentes

    elif qualificacao == 'Participação em grupos, equipes, comissões e projetos especiais, no âmbito do Município do Recife, formalizados por ato oficial.':
        pontos = 5
    elif qualificacao == 'Exercício de cargos comissionados e funções gratificadas, ocupados, exclusivamente, no âmbito do Poder Executivo Municipal.':
        if tempo >= 6:
            pontos = (tempo // 6) * 10
            if pontos > MAX_PONTOS_PERIODO[qualificacao]:  # Limite máximo
                pontos = MAX_PONTOS_PERIODO[qualificacao]
        horas_excedentes = 0

    return pontos, horas_excedentes

def calcular_pontos_cursos_aprovados(usuario_id):
    certificados_aprovados = Certificado.query.filter_by(usuario_id=usuario_id, aprovado=True).all()
    progressoes = {qualificacao: {'pontos': 0, 'progressao': 0, 'horas_excedentes': 0} for qualificacao in QUALIFICACOES}

    for certificado in certificados_aprovados:
        qualificacao = certificado.qualificacao

        progressoes[qualificacao]['progressao'] += certificado.progressao
        progressoes[qualificacao]['pontos'] += certificado.pontos
        progressoes[qualificacao]['horas_excedentes'] += certificado.horas_excedentes

        # Calcular pontos adicionais a partir das horas excedentes
        if qualificacao == 'Cursos, seminários, congressos e oficinas realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            while progressoes[qualificacao]['horas_excedentes'] >= 20:
                progressoes[qualificacao]['horas_excedentes'] -= 20
                progressoes[qualificacao]['pontos'] += 2
        elif qualificacao == 'Cursos de atualização realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            if progressoes[qualificacao]['horas_excedentes'] >= 40:
                progressoes[qualificacao]['horas_excedentes'] -= 40
                progressoes[qualificacao]['pontos'] += 5
        elif qualificacao == 'Cursos de aperfeiçoamento realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            if progressoes[qualificacao]['horas_excedentes'] >= 180:
                progressoes[qualificacao]['horas_excedentes'] -= 180
                progressoes[qualificacao]['pontos'] += 10
        elif qualificacao == 'Cursos de graduação e especialização realizados em instituição pública ou privada, reconhecida pelo MEC.':
            if progressoes[qualificacao]['horas_excedentes'] >= 360:
                progressoes[qualificacao]['horas_excedentes'] -= 360
                progressoes[qualificacao]['pontos'] += 20
        elif qualificacao == 'Instrutoria ou Coordenação de cursos promovidos pelo Município do Recife.':
            while progressoes[qualificacao]['horas_excedentes'] >= 8:
                progressoes[qualificacao]['horas_excedentes'] -= 8
                progressoes[qualificacao]['pontos'] += 2

    return progressoes


def hash_password(password):
    salt = os.urandom(16)
    hashed = pyscrypt.hash(password=password.encode('utf-8'), salt=salt, N=2048, r=8, p=1, dkLen=32)
    return salt.hex() + ':' + hashed.hex()

def verify_password(stored_password, provided_password):
    try:
        salt, stored_hash = stored_password.split(':', 1)
        salt = bytes.fromhex(salt)
        provided_hash = pyscrypt.hash(password=provided_password.encode('utf-8'), salt=salt, N=2048, r=8, p=1, dkLen=32).hex()
        return stored_hash == provided_hash
    except ValueError as e:
        print(f"Erro ao verificar a senha: {e}")
        return False

def generate_protocol(usuario_id):
    current_year = datetime.now().year
    last_certificate = Certificado.query.filter(
        Certificado.usuario_id == usuario_id,
        Certificado.protocolo.like(f"{current_year}-%")
    ).order_by(Certificado.id.desc()).first()

    if last_certificate:
        last_protocol = last_certificate.protocolo
        last_number = int(last_protocol.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1

    new_protocol = f"{current_year}-{new_number:04d}"
    return new_protocol