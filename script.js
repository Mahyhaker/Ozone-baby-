const categorias = [
    { nome: "Originalidade", peso: 1.5 },
    { nome: "Design", peso: 1.2 },
    { nome: "Utilidade", peso: 1.0 },
    { nome: "Projeto Codificado", peso: 1.5 },
    { nome: "Produto de Mercado", peso: 1.3 },
    { nome: "Viabilidade", peso: 1.4 },
    { nome: "Pitch", peso: 1.1 }
];

const opcoes = [
    { texto: "Muito Ruim", valor: 1 },
    { texto: "Ruim", valor: 2 },
    { texto: "Razoável", valor: 3 },
    { texto: "Bom", valor: 4 },
    { texto: "Muito Bom", valor: 5 }
];

let equipeCount = 0;

function carregarEquipes() {
    const equipesSalvas = JSON.parse(localStorage.getItem('equipes')) || [];
    equipeCount = equipesSalvas.length;
    equipesSalvas.forEach(equipe => adicionarEquipe(equipe));
}

function salvarEquipes() {
    const equipes = [];
    for (let i = 1; i <= equipeCount; i++) {
        const nomeEquipe = document.getElementById(`nomeEquipe${i}`).value;
        if (!nomeEquipe) continue;

        const votos = categorias.reduce((acc, categoria) => {
            const valor = parseInt(document.getElementById(`${categoria.nome}${i}`).value);
            acc[categoria.nome] = valor;
            return acc;
        }, {});
        const notaTotal = calcularNotaTotal(votos);
        equipes.push({ nomeEquipe, ...votos, notaTotal });
    }
    localStorage.setItem('equipes', JSON.stringify(equipes));
}

function adicionarEquipe(equipe = null) {
    equipeCount++;
    const container = document.getElementById('equipesContainer');
    const equipeDiv = document.createElement('div');
    equipeDiv.className = 'equipe';
    equipeDiv.id = `equipe${equipeCount}`;
    equipeDiv.innerHTML = `
        <h2>Equipe ${equipeCount} <button type="button" class="btn btn-edit" onclick="editarEquipe(${equipeCount})">Editar</button></h2>
        <label for="nomeEquipe${equipeCount}">Nome da Equipe:</label>
        <input type="text" id="nomeEquipe${equipeCount}" value="${equipe ? equipe.nomeEquipe : ''}" required>
        ${categorias.map(categoria => `
            <div>
                <label>${categoria.nome}:</label>
                <select id="${categoria.nome}${equipeCount}">
                    ${opcoes.map(opcao => `
                        <option value="${opcao.valor}" ${equipe && equipe[categoria.nome] == opcao.valor ? 'selected' : ''}>
                            ${opcao.texto}
                        </option>`).join('')}
                </select>
            </div>
        `).join('')}
    `;
    container.appendChild(equipeDiv);
}

function editarEquipe(id) {
    const equipeDiv = document.getElementById(`equipe${id}`);
    const nomeEquipe = document.getElementById(`nomeEquipe${id}`).value;

    // Lógica para editar a equipe (por exemplo, permitir alteração das notas)
    categorias.forEach(categoria => {
        const selectElement = document.getElementById(`${categoria.nome}${id}`);
        selectElement.disabled = !selectElement.disabled; // Alterna entre habilitar e desabilitar o select
    });
}

document.getElementById('votacaoForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Impede o envio padrão do formulário

    const resultados = [];
    let valido = true;

    for (let i = 1; i <= equipeCount; i++) {
        const nomeEquipe = document.getElementById(`nomeEquipe${i}`).value;
        if (!nomeEquipe) {
            valido = false;
            alert(`Por favor, preencha o nome da equipe ${i}.`);
            break;
        }

        const votos = categorias.reduce((acc, categoria) => {
            const valor = parseInt(document.getElementById(`${categoria.nome}${i}`).value);
            acc[categoria.nome] = valor;
            return acc;
        }, {});
        const notaTotal = calcularNotaTotal(votos);
        resultados.push({ nomeEquipe, ...votos, notaTotal });
    }

    if (valido) {
        fetch('http://127.0.0.1:5000/votar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(resultados)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            salvarEquipes(); // Salva as equipes após o envio dos dados
        })
        .catch(error => {
            console.error('Erro ao enviar os votos:', error);
        });
    }
});

function calcularNotaTotal(votos) {
    return categorias.reduce((acc, categoria) => {
        return acc + (votos[categoria.nome] * categoria.peso);
    }, 0);
}

document.addEventListener('DOMContentLoaded', carregarEquipes); // Carrega as equipes ao inicializar a página
