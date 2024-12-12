from app import app, db
from flask import render_template, redirect, url_for, flash, session, request, jsonify, send_from_directory
from models import Usuario, Certificado, Message
from utils import requires_admin, login_required, calcular_pontos_total, generate_protocol, verify_password, hash_password, MAX_PONTOS_PERIODO
from forms import UploadForm
import os
from werkzeug.utils import secure_filename




# Rotas
@app.route('/')
def index():
    return render_template('home.html', titulo='Bem-vindo ao Certification')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    usuario = request.form['usuario']
    senha = request.form['senha']
    usuario_db = Usuario.query.filter_by(matricula=usuario).first()

    if usuario_db and verify_password(usuario_db.senha, senha):
        session['usuario_logado'] = usuario_db.id
        session['usuario_role'] = usuario_db.role

        flash(f'{usuario_db.nome} logado com sucesso!')
        return redirect(url_for('certificados') if usuario_db.role == 'admin' else url_for('upload'))
    else:
        flash('Usuário ou senha inválidos.')
        return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    session.pop('usuario_role', None)
    flash('Logout efetuado com sucesso!')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        usuario_id = session.get('usuario_logado')
        periodo_de = form.periodo_de.data
        periodo_ate = form.periodo_ate.data

        # Dados do certificado enviado
        certificado_data = {
            'qualificacao': form.qualificacao.data,
            'horas': form.horas.data,
            'quantidade': form.quantidade.data,
            'ano_conclusao': form.ano_conclusao.data,
            'ato_normativo': form.ato_normativo.data,
            'tempo': form.tempo.data,
        }

        # Calcular pontos e horas para este envio específico
        progressoes = calcular_pontos_total(usuario_id, certificados=[certificado_data])
        pontos = progressoes[form.qualificacao.data]['pontos']
        horas_excedentes = progressoes[form.qualificacao.data]['horas_excedentes']

        # Criar um novo certificado (nova linha no banco)
        protocolo = generate_protocol(usuario_id)

        novo_certificado = Certificado(
            protocolo=protocolo,
            qualificacao=form.qualificacao.data,
            periodo_de=periodo_de,
            periodo_ate=periodo_ate,
            carga_horaria=form.horas.data,
            quantidade=form.quantidade.data,
            pontos=pontos,
            horas_excedentes=horas_excedentes,
            ano_conclusao=form.ano_conclusao.data,
            ato_normativo=form.ato_normativo.data,
            tempo=form.tempo.data,
            descricao=form.descricao.data,
            filename=secure_filename(form.certificate.data.filename),
            usuario_id=usuario_id
        )

        db.session.add(novo_certificado)
        db.session.commit()

        flash('Certificado enviado com sucesso! Aguardando aprovação.', 'success')
        return redirect(url_for('certificados'))

    return render_template('upload.html', form=form)




@app.route('/certificados')
@login_required
@requires_admin
def certificados():
    certificado_index = request.args.get('index', 0, type=int)
    total_certificados = Certificado.query.filter_by(aprovado=False, recusado=False).count()
    certificados = Certificado.query.filter_by(aprovado=False, recusado=False).all()

    certificado_atual = certificados[certificado_index] if certificados else None
    next_index = certificado_index + 1 if certificado_index < total_certificados - 1 else None
    prev_index = certificado_index - 1 if certificado_index > 0 else None

    return render_template(
        'certificados.html',
        certificado_atual=certificado_atual,
        certificados=certificados,
        next_index=next_index,
        prev_index=prev_index
    )

@app.route('/certificados_pendentes')
@login_required
def certificados_pendentes():
    usuario_id = session.get('usuario_logado')
    certificados = Certificado.query.filter_by(usuario_id=usuario_id, aprovado=False).all()
    return render_template('certificados_pendentes.html', certificados=certificados)

@app.route('/certificados_aprovados')
@login_required
def certificados_aprovados():
    usuario_id = session.get('usuario_logado')
    certificados = Certificado.query.filter_by(usuario_id=usuario_id, aprovado=True).all()
    return render_template('certificados_aprovados.html', certificados=certificados)

@app.route('/painel')
@login_required
def painel():
    usuario_id = session.get('usuario_logado')
    usuario = db.session.get(Usuario, usuario_id)
    return redirect(url_for('certificados') if usuario.role == 'admin' else url_for('upload'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'O arquivo {filename} foi deletado com sucesso!')
    else:
        flash(f'O arquivo {filename} não foi encontrado.')
    return redirect(url_for('upload'))

@app.route('/signup')
@requires_admin
def signup():
    return render_template('signup.html')

@app.route('/cadastrar', methods=['POST'])
@requires_admin
def cadastrar():
    try:
        matricula = request.form['matricula']
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        role = request.form['role']

        hashed_senha = hash_password(senha)

        novo_usuario = Usuario(matricula=matricula, nome=nome, email=email, senha=hashed_senha, role=role)
        db.session.add(novo_usuario)
        db.session.commit()
        flash(f'Usuário {nome} cadastrado com sucesso!')
        return redirect('/login')
    except Exception as e:
        print(e)
        db.session.rollback()
        flash(f'Erro ao cadastrar usuário: {str(e)}')
        return redirect('/signup')

@app.route('/usuarios')
@requires_admin
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@requires_admin
def editar_usuario(id):
    usuario = db.session.get(Usuario, id)
    if request.method == 'POST':
        usuario.matricula = request.form['matricula']
        usuario.nome = request.form['nome']
        usuario.email = request.form['email']
        if request.form['senha']:
            usuario.senha = hash_password(request.form['senha'])
        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!')
            return redirect(url_for('listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}')
    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/deletar_usuario/<int:id>', methods=['POST'])
@requires_admin
def deletar_usuario(id):
    usuario = db.session.get(Usuario, id)
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário deletado com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar usuário: {str(e)}')
    return redirect(url_for('listar_usuarios'))

@app.route('/cursos')
@login_required
def cursos():
    usuario_id = session.get('usuario_logado')

    # Chamada da função com persistência no banco
    progressoes = calcular_pontos_total(usuario_id, persist=True)

    cursos_list = [
        {
            'nome': nome,
            'pontos': data['pontos'],
            'horas_excedentes': data['horas_excedentes']
        } for nome, data in progressoes.items()
    ]

    return render_template('cursos.html', cursos=cursos_list)




@app.route('/aprovar/<int:certificado_id>', methods=['POST'])
@requires_admin
def aprovar_certificado(certificado_id):
    certificado = db.session.get(Certificado, certificado_id)
    if certificado and not certificado.aprovado:
        certificado.aprovado = True

        try:
            # Sincronizar pontos no banco após aprovação
            calcular_pontos_total(certificado.usuario_id, persist=True)
            db.session.commit()
            flash('Certificado aprovado e pontos sincronizados!')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao aprovar certificado: {str(e)}')
    else:
        flash('Certificado já aprovado ou não encontrado.')
    return redirect(url_for('certificados'))



@app.route('/recusar_certificado/<int:certificado_id>', methods=['POST'])
@requires_admin
def recusar_certificado(certificado_id):
    certificado = db.session.get(Certificado, certificado_id)
    if certificado:
        certificado.aprovado = False
        certificado.recusado = True
        db.session.commit()
        flash('Certificado recusado com sucesso!')
    else:
        flash('Certificado não encontrado.')
    return redirect(url_for('certificados'))

@app.route('/api/mensagens_usuario', methods=['POST'])
@login_required
def api_post_mensagens_usuario():
    data = request.get_json()
    mensagem_content = data.get('mensagem')
    sender = session.get('usuario_logado')
    recipient = 'admin'

    if not mensagem_content:
        return jsonify({'error': 'Mensagem não pode ser vazia'}), 400

    nova_mensagem = Message(content=mensagem_content, sender=sender, recipient=recipient)
    db.session.add(nova_mensagem)
    db.session.commit()

    return jsonify({'success': 'Mensagem enviada com sucesso'})

@app.route('/api/mensagens', methods=['GET'])
def api_get_mensagens():
    if not session.get('usuario_logado') or session.get('usuario_role') != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403

    mensagens = Message.query.filter_by(recipient='admin').order_by(Message.timestamp.desc()).all()
    mensagens_json = [{'sender': m.sender, 'content': m.content, 'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for m in mensagens]
    return jsonify(mensagens_json)

@app.route('/progressoes', methods=['GET', 'POST'])
@login_required
def progressoes():
    usuarios = Usuario.query.filter(Usuario.role != 'admin').all()
    usuario_id = int(request.form.get('usuario') or session.get('usuario_logado'))

    # Chamada da nova função consolidada
    progressoes = calcular_pontos_total(usuario_id)
    errors = {}

    if request.method == 'POST':
        for i, (qualificacao, dados) in enumerate(progressoes.items()):
            adicionar_key = f'adicionar_{i + 1}'
            if adicionar_key in request.form:
                try:
                    progressao_valor = int(request.form.get(adicionar_key, '0'))
                except ValueError:
                    flash("Valor inválido para progressão.", "danger")
                    continue

                # Verifica se o valor da progressão é maior que 0 antes de continuar
                if progressao_valor <= 0:
                    flash(f"Erro: Valor de progressão deve ser maior que 0 para '{qualificacao}'.", "danger")
                    continue

                pontos_disponiveis = progressoes[qualificacao]['pontos']

                if progressao_valor > pontos_disponiveis:
                    flash(f"Erro: Você tentou usar mais pontos do que estão disponíveis para '{qualificacao}'.", "danger")
                    continue

                # Atualizar os certificados aprovados
                certificados_aprovados_qualificacao = Certificado.query.filter_by(
                    usuario_id=usuario_id, aprovado=True, qualificacao=qualificacao
                ).all()

                for certificado in certificados_aprovados_qualificacao:
                    if progressao_valor <= 0:
                        break

                    if certificado.pontos > 0:
                        restante = min(progressao_valor, certificado.pontos)
                        certificado.progressao += restante
                        certificado.pontos -= restante
                        progressoes[qualificacao]['pontos'] -= restante
                        progressoes[qualificacao]['progressao'] += restante
                        progressao_valor -= restante
                        db.session.add(certificado)

                db.session.commit()
                flash(f"Pontos da qualificação '{qualificacao}' atualizados com sucesso!", "success")

    # Recalcular progresso atualizado
    progressoes = calcular_pontos_total(usuario_id)

    return render_template(
        'progressoes.html',
        progressoes=progressoes,
        usuarios=usuarios,
        usuario_selecionado=usuario_id,
        errors=errors
    )