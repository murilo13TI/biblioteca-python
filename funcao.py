from flask import Flask, jsonify, request
from main import app, con
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


