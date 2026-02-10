from flask import Flask, jsonify, request
from main import app, con
from funcao import verificar_senha
from flask_bcrypt import generate_password_hash, check_password_hash

@app.route('/listar_livro', methods=['GET'])
def listar_livro():
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
    try:
        dados = request.get_json()

        nome_livro = dados.get('nome_livro')
        autor = dados.get('autor')
        ano_publicado = dados.get('ano_publicacao')

        cur = con.cursor()

        cur.execute('select 1 from livro where nome_livro = ?', (nome_livro,))
        if cur.fetchone():
            return jsonify({'error':'Livro já cadastrado'}), 400

        cur.execute("""insert into livro(nome_livro, autor, ano_publicado)
        values(?,?,?) """, (nome_livro, autor, ano_publicado))

        con.commit()
        return jsonify({
            'message': "Livro cadastrado com sucesso?",
            'livro': {
                'nome_livro': nome_livro,
                'autor': autor,
                'ano_publicado': ano_publicado
            }
        }), 201
    except Exception as e:

        return jsonify({'message': 'Erro ao criar o livro'}), 500
    finally:
        con.close()

@app.route('/editar_livro/<int:id>', methods=['PUT'])
def editar_livro(id):
    cur = con.cursor()
    cur.execute("""select id_livro, nome_livro, autor, ano_publicado
                     from livro 
                     where id_livro = ?""", (id,))
    tem_livro = cur.fetchone()

    if not tem_livro:
        cur.close()
        return jsonify({"error": "Livro não encontrado"}), 404

    dados = request.get_json()
    nome_livro = dados.get('nome_livro')
    autor = dados.get('autor')
    ano_publicado = dados.get('ano_publicado')

    cur.execute("""update livro set nome_livro = ?, autor = ? , ano_publicado = ? where id_livro = ?""",
                (nome_livro, autor, ano_publicado, id))

    con.commit()
    cur.close()

    return jsonify({"message": "Livro atualizado com sucesso!",
                    "livro": {
                    "id_livro": id,
                    "nome_livro": nome_livro,
                    "autor": autor,
                    "ano_publicado": ano_publicado
                    }
                    })

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

@app.route('/login', methods=['GET'])
def login():
    cur = con.cursor()
    try:
        dados = request.get_json()

        email = dados.get('email')
        senha = dados.get('senha')

        cur.execute("select id_usuario , nome , email, senha from usuario where = ?", (email,))


        if email != email and check_password_hash(senha) != senha:
            return jsonify({'error': 'O email ou a senha não se coincidem'})

        con.close()

        if email == email and check_password_hash(senha) == senha:
            return jsonify({'message':'Usuário logado com sucesso'})
            cur.close()

    except Exception as e:
        return jsonify({'error':'Não conseguimos logar a conta'})
    finally:
        con.close()

@app.route('/edita_usuario', methods=['PUT'])
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

@app.route('/deletar_usuario', methods=['DELETE'])
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



