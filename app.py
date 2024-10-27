from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this in production
CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    votes = db.relationship('Vote', backref='user', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('team_name', 'category', 'user_id', name='unique_vote'),
    )

with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Username already exists"}), 400
    
    user = User(
        username=data['username'],
        password_hash=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.username)
        return jsonify({"token": access_token, "username": user.username}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/vote', methods=['POST'])
@jwt_required()
def submit_vote():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    data = request.json
    
    try:
        for category, score in data['votes'].items():
            existing_vote = Vote.query.filter_by(
                user_id=current_user.id,
                team_name=data['teamName'],
                category=category
            ).first()
            
            if existing_vote:
                existing_vote.score = score
            else:
                new_vote = Vote(
                    team_name=data['teamName'],
                    category=category,
                    score=score,
                    user_id=current_user.id
                )
                db.session.add(new_vote)
        
        db.session.commit()
        return jsonify({"message": "Votes submitted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400

@app.route('/results', methods=['GET'])
def get_results():
    teams = {}
    votes = Vote.query.all()
    
    for vote in votes:
        if vote.team_name not in teams:
            teams[vote.team_name] = {
                'name': vote.team_name,
                'categories': {},
                'totalScore': 0,
                'voterCount': set()
            }
        
        if vote.category not in teams[vote.team_name]['categories']:
            teams[vote.team_name]['categories'][vote.category] = []
            
        teams[vote.team_name]['categories'][vote.category].append(vote.score)
        teams[vote.team_name]['voterCount'].add(vote.user_id)
    
    results = []
    for team_name, team_data in teams.items():
        avg_scores = {}
        total_score = 0
        weights = {
            "Originalidade": 1.5,
            "Design": 1.2,
            "Utilidade": 1.0,
            "Projeto Codificado": 1.5,
            "Produto de Mercado": 1.3,
            "Viabilidade": 1.4,
            "Pitch": 1.1
        }
        
        for category, scores in team_data['categories'].items():
            avg = sum(scores) / len(scores)
            avg_scores[category] = avg
            total_score += avg * weights.get(category, 1)
        
        results.append({
            'teamName': team_name,
            'scores': avg_scores,
            'totalScore': round(total_score, 2),
            'voterCount': len(team_data['voterCount'])
        })
    
    return jsonify(sorted(results, key=lambda x: x['totalScore'], reverse=True)), 200

if __name__ == '__main__':
    app.run(debug=True)