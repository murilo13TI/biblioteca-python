from flask import Flask, jsonify, request
from main import app, con
import jwt
import datetime
from email.mime.text import MIMEText
import smtplib

senha_secreta = app.config['SECRET_KEY']
def gerar_token(id_usuario):
    payload = {
        'id_usuario': id_usuario,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    token = jwt.encode(payload,senha_secreta,algorithm='HS256')
    return token

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('bearer '):]
    else:
        return token

def verificar_senha(senha):

    if len(senha) < 8:
        return False

    tem_maiuscula = False
    tem_minuscula = False
    tem_numero = False
    tem_especial = False

    caracteres_especiais = '!@#$%&*§^~?ªº'

    for char in senha:
        if char.isupper():
            tem_maiuscula = True
        elif char.islower():
            tem_minuscula = True
        elif char.isdigit():
            tem_numero = True
        elif char in caracteres_especiais:
            tem_especial = True

    if tem_maiuscula and tem_minuscula and tem_numero and tem_especial:
        return True

    return False

def enviando_email(destinatario, assunto, mensagem):
    user = "muriloalmeidasilva73@gmail.com"
    senha = "ocoo ziqa djtk vops"

    msg = MIMEText(mensagem)
    msg['Subject'] = assunto
    msg['From'] = user
    msg['To'] = destinatario

    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(user, senha)
    server.send_message(msg)
    server.quit()