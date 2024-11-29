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

def calcular_pontos_total(usuario_id, certificados=None, persist=False):
    """
    Calcula os pontos totais, progressões e horas excedentes para um usuário.
    Pode persistir os valores no banco de dados, se solicitado.
    """
    if certificados is None:
        # Se os certificados não forem fornecidos, busca os certificados aprovados no banco de dados
        certificados = Certificado.query.filter_by(usuario_id=usuario_id, aprovado=True).all()

    progressoes = {qualificacao: {'pontos': 0, 'progressao': 0, 'horas_excedentes': 0} for qualificacao in QUALIFICACOES}

    for certificado in certificados:
        if isinstance(certificado, dict):
            qualificacao = certificado.get('qualificacao', '')
            horas = certificado.get('horas', 0)
            tempo = certificado.get('tempo', 0)
            progressao = 0
        else:
            qualificacao = certificado.qualificacao
            horas = certificado.carga_horaria or 0
            tempo = certificado.tempo or 0
            progressao = certificado.progressao or 0

        if qualificacao == 'Cursos, seminários, congressos e oficinas realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            progressoes[qualificacao]['pontos'] += (horas // 20) * 2
            progressoes[qualificacao]['horas_excedentes'] += horas % 20

        elif qualificacao == 'Cursos de atualização realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            progressoes[qualificacao]['pontos'] += 5 if horas >= 40 else 0
            progressoes[qualificacao]['horas_excedentes'] += max(horas - 40, 0)

        elif qualificacao == 'Cursos de aperfeiçoamento realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            progressoes[qualificacao]['pontos'] += 10 if horas >= 180 else 0
            progressoes[qualificacao]['horas_excedentes'] += max(horas - 180, 0)

        elif qualificacao == 'Cursos de graduação e especialização realizados em instituição pública ou privada, reconhecida pelo MEC.':
            progressoes[qualificacao]['pontos'] += 20 if horas >= 360 else 0
            progressoes[qualificacao]['horas_excedentes'] += max(horas - 360, 0)

        elif qualificacao == 'Mestrado, doutorado e pós-doutorado realizados em instituição pública ou privada, reconhecida pelo MEC.':
            progressoes[qualificacao]['pontos'] += 30

        elif qualificacao == 'Instrutoria ou Coordenação de cursos promovidos pelo Município do Recife.':
            progressoes[qualificacao]['pontos'] += (horas // 8) * 2
            progressoes[qualificacao]['horas_excedentes'] += horas % 8

        elif qualificacao == 'Participação em grupos, equipes, comissões e projetos especiais, no âmbito do Município do Recife, formalizados por ato oficial.':
            progressoes[qualificacao]['pontos'] += 5

        elif qualificacao == 'Exercício de cargos comissionados e funções gratificadas, ocupados, exclusivamente, no âmbito do Poder Executivo Municipal.':
            progressoes[qualificacao]['pontos'] += (tempo // 6) * 10 if tempo >= 6 else 0

        progressoes[qualificacao]['progressao'] += progressao

    for qualificacao, dados in progressoes.items():
        horas_excedentes = dados['horas_excedentes']
        pontos_por_hora = 0
        limite_horas = 0

        if qualificacao == 'Cursos, seminários, congressos e oficinas realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            pontos_por_hora = 2
            limite_horas = 20
        elif qualificacao == 'Cursos de atualização realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            pontos_por_hora = 5
            limite_horas = 40
        elif qualificacao == 'Cursos de aperfeiçoamento realizados, promovidos, articulados ou admitidos pelo Município do Recife.':
            pontos_por_hora = 10
            limite_horas = 180
        elif qualificacao == 'Cursos de graduação e especialização realizados em instituição pública ou privada, reconhecida pelo MEC.':
            pontos_por_hora = 20
            limite_horas = 360
        elif qualificacao == 'Instrutoria ou Coordenação de cursos promovidos pelo Município do Recife.':
            pontos_por_hora = 2
            limite_horas = 8

        while horas_excedentes >= limite_horas and limite_horas > 0:
            dados['pontos'] += pontos_por_hora
            horas_excedentes -= limite_horas

        dados['horas_excedentes'] = horas_excedentes

        if persist:
            # Atualizar no banco de dados os certificados aprovados
            certificados_qualificacao = Certificado.query.filter_by(
                usuario_id=usuario_id, aprovado=True, qualificacao=qualificacao
            ).all()

            for certificado in certificados_qualificacao:
                certificado.pontos = dados['pontos']
                certificado.horas_excedentes = dados['horas_excedentes']
                db.session.add(certificado)

    if persist:
        db.session.commit()

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