import threading
import  os
import jwt
from flask import Flask, jsonify, request, Response, make_response
import pygal

from main import app, con
from flask_bcrypt import generate_password_hash, check_password_hash
from funcao import verificar_senha, gerar_token, remover_bearer, enviando_email
from fpdf import FPDF
from flask import send_file

senha = app.config['SECRET_KEY']


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


@app.route('/listar_livro', methods=['GET'])
def listar_livro():
    token = request.headers.get('authorization')
    if not token:
        return jsonify({'menssage':'token de autentificação necessário'}), 401

    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, senha, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({"message":"Token expirado"}),401
    except jwt.InvalidTokenError:
        return jsonify({"message":"Token invalido"}),401

    try:
        cur = con.cursor()
        cur.execute('SELECT id_livro, nome_livro, autor, ano_publicado FROM livro')
        livros = cur.fetchall()

        livro_lista = []
        for livro in livros:
            livro_lista.append({
                'id_livro': livro[0],
                'nome_livro': livro[1],
                'autor': livro[2],
                'ano_publicado': livro[3]
            })

        return jsonify(
            mensagem='lista de livros',
            livros=livro_lista
        )

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500

    finally:
        con.close()


@app.route('/criar_livro', methods=['POST'])
def criar_livro():
    # token = request.headers.get("Authorization")
    token = request.cookies.get("access_token")

    if not token:
        return jsonify({"erro": "Token necessário"}), 401

    token = remover_bearer(token)

    try:
        jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
    except jwt.ExpiredSignatureError:
        return jsonify({'mensagem': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'mensagem': 'Token inválido'}), 401

    cur = con.cursor()

    try:
        titulo = request.form.get("titulo")
        autor = request.form.get("autor")
        ano_publicacao = request.form.get("ano_publicacao")
        imagem = request.files.get("imagem")

        if not titulo or not autor or not ano_publicacao:
            return jsonify({"erro": "Campos obrigatórios"}), 400

        cur.execute(
            "INSERT INTO livro (nome_livro, autor, ano_publicado) VALUES (?, ?, ?) RETURNING id_livro",
            (titulo, autor, ano_publicacao)
        )
        id_livro = cur.fetchone()[0]
        con.commit()

        if imagem:
            pasta = os.path.join(app.config['UPLOAD_FOLDER'], "livros")
            os.makedirs(pasta, exist_ok=True)
            nome = f"{id_livro}.jpg"
            caminho = os.path.join(pasta, nome)
            imagem.save(caminho)

        return jsonify({
            "mensagem": "Livro criado",
            "id_livro": id_livro
        }), 201

    except Exception as e:
        con.rollback()
        return jsonify({"erro": str(e)}), 500
    finally:
        cur.close()



@app.route('/livro/<int:id>', methods=['PUT'])
def editar_livro(id):
    data = request.get_json() or {}
    titulo = data.get("titulo")
    autor = data.get("autor")
    ano = data.get("ano_publicacao")

    cur = con.cursor()

    cur.execute("""
        UPDATE livro
        SET nome_livro=?, autor=?, ano_publicado=?
        WHERE id_livro=?
    """, (titulo, autor, ano, id))

    con.commit()
    cur.close()

    return jsonify({"mensagem": "Livro atualizado"})


@app.route('/deletar_livro/<int:id>', methods=['DELETE'])
def deletar_livro(id):
    cur = con.cursor()

    cur.execute('select 1 from livro where id_livro = ?', (id,))
    if not cur.fetchone():
        cur.close()
        return jsonify({"error": " Livro não encontrado"}), 404

    cur.execute('delete from livros where id = ?', (id,))
    con.commit()
    cur.close()

    return jsonify({"message": "livro deletado com sucesso!", 'id_livro': id})

@app.route('/cadastro', methods=['POST'])
def cadastro():
    cur = con.cursor()

    try:
        dados = request.get_json()

        nome_usuario = dados.get('nome_usuario')
        email = dados.get('email')
        senha = dados.get('senha')


        cur.execute("SELECT id_usuario FROM usuario WHERE email = ?", (email,))
        usuario = cur.fetchone()

        if usuario:
            return jsonify({'error': 'Já existe uma conta com este email'}), 400

        if not verificar_senha(senha):
            return jsonify({"erro": "A senha não atinge os requisitos necessários"}), 400

        hash_senha = generate_password_hash(senha).decode('utf-8')

        cur.execute(
            "INSERT INTO usuario (nome_usuario, email, senha) VALUES (?, ?, ?)",
            (nome_usuario, email, hash_senha)
        )

        con.commit()
        return jsonify({"message": "Cadastro feito com sucesso!"}), 201

    except Exception as e:
        print(e)  # ajuda MUITO no debug
        return jsonify({"error": "Não foi possível a criação da conta"}), 500

    finally:
        cur.close()
@app.route('/login', methods=['POST'])
def login():
    cur = con.cursor()
    try:
        dados = request.get_json()

        email = dados.get('email')
        senha = dados.get('senha')

        cur.execute(
            "SELECT id_usuario, nome_usuario, email, senha FROM usuario WHERE email = ?",
            (email,)
        )

        usuario = cur.fetchone()

        if not usuario:
            return jsonify({'message': 'Usuário não encontrado'}), 404

        id_usuario = usuario[0]
        senha_hash = usuario[3]

        if check_password_hash(senha_hash, senha):
            token = gerar_token(id_usuario)

            resp = make_response(jsonify({'mensagem': "Logado com sucesso!"}), 200)

            resp.set_cookie(
                "access_token",
                token,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
                max_age=3600
            )

            return resp

        return jsonify({'message': 'Dados incorretos'}), 401

    except Exception as e:
        return jsonify({'error': f'Não conseguimos logar a conta {e}'}), 500

    finally:
        cur.close()

@app.route('/edita_usuario/<int:id_usuario>', methods=['PUT'])
def editar_usuario(id):

    cur = con.cursor()
    cur.execute("""select id_usuario, nome_usuario, email, senha from usuario where id_usuario = ?""", (id,))

    usuario_existe = cur.fetchone()

    if not usuario_existe:
        return jsonify({'error':'Usuario não encontrado'}), 404
        cur.close()

    else:
        dados = request.get_json()
        nome_usuario = dados.get('nome_usuario')
        email = dados.get('email')
        senha = dados.get('senha')

        cur.execute("""update livro set nome_usuario = ?, email = ? , senha = ? where id_usuario = ?""",
                    (nome_usuario, email, senha, id))

        con.commit()
        cur.close()

        return jsonify({"message": "Usuario atualizado com sucesso!",
                        "livro": {
                            "id_usuario": id,
                            "nome_usuario": nome_usuario,
                            "email": email,
                            "senha": senha
                        }
                        })

@app.route('/deletar_usuario/<int:id_usuario>', methods=['DELETE'])
def deletar_usuario():
    cur = con.cursor()

    cur.execute('select 1 from usuario where id_usuario = ?', (id,))
    if not cur.fetchone():
        cur.close()
        return jsonify({"error": " Usuario não encontrado"}), 404

    cur.execute('delete from usuario where id = ?', (id,))
    con.commit()
    cur.close()

    return jsonify({"message": "Usuario deletado com sucesso!", 'id_usuario': id})

@app.route('/gerar_pdf' ,methods=["get"])
def gerar_pdf():
    try:
        cur = con.cursor()
        cur.execute("SELECT id_usuario, nome_usuario, email, senha FROM usuario")
        usuario = cur.fetchall()
        cur.close()

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=16)
        pdf.cell(200, 10, "Relatorio de usuário", ln=True, align='C')
        pdf.ln(5)  # Espaço entre o título e a linha
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Linha abaixo do título
        pdf.ln(5)  # Espaço após a linha
        pdf.set_font("Arial", size=12)
        for usuario in usuario:
            pdf.cell(200, 10, f"ID: {usuario[0]} - {usuario[1]} - {usuario[2]} - {usuario[3]}", ln=True)
        contador_usuario = len(usuario)
        pdf.ln(10)  # Espaço antes do contador
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, f"Total de usuários cadastrados: {contador_usuario}", ln=True, align='C')
        pdf_path = "relatorio_usuario.pdf"
        pdf.output(pdf_path)
        return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
       cur.close()


@app.route('/usuario/<int:id>', methods=['PUT'])
def atualizar_usuario(id):
    dados = request.get_json() or {}

    senha_hash = generate_password_hash(
        dados["senha"]
    ).decode("utf-8")

    cur = con.cursor()

    cur.execute("""
        UPDATE usuario
        SET nome=?, usuario=?, senha=?
        WHERE id=?
    """, (
        dados["nome"],
        dados["usuario"],
        senha_hash,
        id
    ))

    con.commit()
    cur.close()

    return jsonify({"mensagem": "Usuário atualizado"})


@app.route('/gerar_grafico', methods=['GET'])
def gerar_grafico():
    try:
        cur = con.cursor()
        cur.execute("""
        select ano_publicado, count(*) 
        from livro 
        group by ano_publicado 
        order by ano_publicado 
        """)
        graficos = cur.fetchall()

        grafico = pygal.Bar()
        grafico.title = 'Grafico de livros'

        for linha in graficos:
            grafico.add(str(linha[0]), linha[1])
        return Response(grafico.render(), mimetype='image/svg+xml')

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados {e}'}), 500
    finally:
        cur.close()

@app.route('/enviar_email', methods=['POST'])
def enviar_email():
    dados = request.json
    destinatario = dados.get('to')
    assunto = dados.get('subject')
    mensagem = dados.get('message')
    thread = threading.Thread(target=enviando_email, args=(destinatario, assunto, mensagem))
    thread.start()

    return jsonify({'message': 'Email enviado com sucesso!'}) , 200
