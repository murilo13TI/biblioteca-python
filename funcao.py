from flask import Flask, jsonify, request
from main import app, con

@app.route('/cadastrar/', methods=['POST'])
def cadastro():

    try:
