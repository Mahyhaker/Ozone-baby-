// Constants and Configuration
const API_URL = 'http://127.0.0.1:5000';
const ADMIN_USERNAME = 'admin'; // Defina aqui seu nome de usuário de administrador
const CATEGORIES = [
    { name: "Originalidade", weight: 1.5 },
    { name: "Design", weight: 1.2 },
    { name: "Utilidade", weight: 1.0 },
    { name: "Projeto Codificado", weight: 1.5 },
    { name: "Produto de Mercado", weight: 1.3 },
    { name: "Viabilidade", weight: 1.4 },
    { name: "Pitch", weight: 1.1 }
];

const RATINGS = [
    { text: "Muito Ruim", value: 1 },
    { text: "Ruim", value: 2 },
    { text: "Razoável", value: 3 },
    { text: "Bom", value: 4 },
    { text: "Muito Bom", value: 5 }
];

// State Management
let currentUser = null;
let authToken = null;

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
    createVotingForm();
});

// Authentication Functions
function checkAuth() {
    const token = localStorage.getItem('authToken');
    const username = localStorage.getItem('username');
    if (token && username) {
        authToken = token;
        currentUser = username;
        showMainContent();
    }
}

function login(username, password) {
    fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            authToken = data.token;
            currentUser = data.username;
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('username', data.username);
            showMainContent();
            showToast('Login realizado com sucesso!', 'success');
        // Se for admin, mostrar controles de administrador
        if (currentUser === ADMIN_USERNAME) {
            document.querySelectorAll('.admin-controls').forEach(el => el.style.display = 'block');
        }
        } else {
            showToast('Credenciais inválidas!', 'error');
        }
    })
    .catch(error => {
        showToast('Erro ao fazer login!', 'error');
        console.error('Login error:', error);
    });
}

function register(username, password) {
    fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (response.ok) {
            showToast('Registro realizado com sucesso!', 'success');
            toggleAuthForm(); // Switch back to login form
        } else {
            showToast(data.message || 'Erro no registro!', 'error');
        }
    })
    .catch(error => {
        showToast('Erro ao registrar!', 'error');
        console.error('Registration error:', error);
    });
}

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    authToken = null;
    currentUser = null;
    showLoginSection();
}

// UI Functions
function showMainContent() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('mainContent').style.display = 'block';
    document.getElementById('currentUser').textContent = `Olá, ${currentUser}!`;

    updateResults(); // Load initial results
}

function showLoginSection() {
    document.getElementById('loginSection').style.display = 'flex';
    document.getElementById('mainContent').style.display = 'none';
}

function toggleAuthForm() {
    const loginForm = document.getElementById('loginForm').parentElement;
    const registerForm = document.getElementById('registerForm');
    loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
    registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
}

function showTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Section`).classList.add('active');
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Voting Functions
function createVotingForm() {
    const container = document.querySelector('.categories-grid');
    
    CATEGORIES.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-card';
        
        categoryDiv.innerHTML = 
            `<h3>${category.name}</h3>
            <div class="rating-group">
                ${RATINGS.map(rating => 
                    `<div class="rating-option">
                        <input type="radio" 
                               id="${category.name}-${rating.value}" 
                               name="${category.name}" 
                               value="${rating.value}">
                        <label for="${category.name}-${rating.value}">${rating.text}</label>
                    </div>`
                ).join('')}
            </div>`;
        
        container.appendChild(categoryDiv);
    });
}

function submitVotes(event) {
    event.preventDefault();
    
    const teamName = document.getElementById('teamName').value;
    const votes = {};
    
    CATEGORIES.forEach(category => {
        const selectedRating = document.querySelector(`input[name="${category.name}"]:checked`);
        if (selectedRating) {
            votes[category.name] = parseInt(selectedRating.value);
        }
    });
    
    if (Object.keys(votes).length !== CATEGORIES.length) {
        showToast('Por favor, avalie todas as categorias!', 'error');
        return;
    }
    
    fetch(`${API_URL}/vote`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
            teamName,
            votes
        })
    })
    .then(response => response.json())
    .then(data => {
        showToast('Votos registrados com sucesso!', 'success');
        document.getElementById('votingForm').reset();
        updateResults();
    })
    .catch(error => {
        showToast('Erro ao registrar votos!', 'error');
        console.error('Voting error:', error);
    });
}

function updateResults() {
    const container = document.querySelector('.results-container');
    container.innerHTML = '<div class="loading"></div>';
    
    fetch(`${API_URL}/results`)
        .then(response => response.json())
        .then(results => {
            container.innerHTML = results.map(team => 
                `<div class="team-result fade-in">
                    <div class="team-header">
                        <h3 class="team-name">${team.teamName}</h3>
                        <span class="total-score">${team.totalScore.toFixed(1)} pontos</span>
                         ${currentUser === ADMIN_USERNAME ? 
                            `<button class="delete-btn admin-controls" onclick="deleteTeam('${team.teamName}')">Excluir Equipe</button>` 
                            : ''}
                    </div>
                    <div class="scores-grid">
                        ${Object.entries(team.scores).map(([category, score]) => 
                            `<div class="score-card">
                                <div class="score-category">${category}</div>
                                <div class="score-value">${score.toFixed(1)}</div>
                            </div>`
                        ).join('')}
                    </div>
                    <div class="voter-count">
                        ${team.voterCount} avaliador${team.voterCount !== 1 ? 'es' : ''}
                    </div>
                </div>`
            ).join('');
        })
        .catch(error => {
            container.innerHTML = '<p class="error">Erro ao carregar resultados.</p>';
            console.error('Results error:', error);
        });
}

// Event Listeners Setup
function setupEventListeners() {
    document.getElementById('loginForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        login(username, password);
    });
    
    document.getElementById('signupForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('newUsername').value;
        const password = document.getElementById('newPassword').value;
        register(username, password);
    });
    // Setup tab switching
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const tabName = e.target.getAttribute('data-tab');
            showTab(tabName);
        });
    });

    document.getElementById('votingForm').addEventListener('submit', submitVotes);
}

// Admin Controls
function setupEventListeners() {
    // Setup tab switching
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const tabName = e.target.getAttribute('data-tab');
            showTab(tabName);
        });
    });

    document.getElementById('loginForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        login(username, password);
    });

    document.getElementById('votingForm').addEventListener('submit', submitVotes);

    // Add event listener for delete team button
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const teamName = e.target.getAttribute('data-team-name');
            deleteTeam(teamName);
        });
    });
}

function deleteTeam(teamName) {
    if (!confirm(`Tem certeza que deseja excluir a equipe ${teamName}?`)) {
        return;
    }

    fetch(`${API_URL}/team/${teamName}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        showToast('Equipe excluída com sucesso!', 'success');
        updateResults();
    })
    .catch(error => {
        showToast('Erro ao excluir equipe!', 'error');
        console.error('Delete error:', error);
    });
}
    
    

