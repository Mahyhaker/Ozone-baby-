from flask import Flask, request, jsonify
# pip install Flask-Cors
from flask_cors import CORS

# Inicializa a aplicação Flask
app = Flask(__name__)

# Permite requisições de outros domínios
CORS(app)

# Lista para armazenar os votos
votos = []

# Rota para receber votos via método POST
@app.route('/votar', methods=['POST'])
def votar():
    data = request.json  # Obtém os dados da requisição
    for voto in data:
        # Verifica se a equipe já existe na lista de votos
        existente = next((item for item in votos if item['nomeEquipe'] == voto['nomeEquipe']), None)
        if existente:
            # Atualiza os dados da equipe existente
            existente.update(voto)
        else:
            # Adiciona a nova equipe à lista de votos
            votos.append(voto)
    return jsonify({"message": "Voto recebido com sucesso!"}), 200

# Rota para exibir os resultados das votações via método GET
@app.route('/resultados', methods=['GET'])
def resultados():
    # Ordena os votos por nota total em ordem decrescente
    ranking = sorted(votos, key=lambda x: x['notaTotal'], reverse=True)
    return jsonify(ranking), 200

# Inicia a aplicação Flask em modo de debug
if __name__ == "__main__":
    app.run(debug=True)
