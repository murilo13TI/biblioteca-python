from flask import Flask, jsonify, request
from main import app, con

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
        cur.close()

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
        cur.close()

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