"""
FAESA Voting System — app.py
Flask backend with JWT auth, SQLite, and vote management.
Admin registers teams; voters only choose from the list.
"""

import os
from datetime import timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="frontend", static_url_path="")

app.config.update(
    SQLALCHEMY_DATABASE_URI       = os.environ.get("DATABASE_URL", "sqlite:///voting.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS= False,
    JWT_SECRET_KEY                = os.environ.get("JWT_SECRET_KEY", "change-me-in-production"),
    JWT_ACCESS_TOKEN_EXPIRES      = timedelta(hours=8),
)

CORS(app, resources={r"/*": {"origins": "*"}})

db  = SQLAlchemy(app)
jwt = JWTManager(app)

# ── Constants ─────────────────────────────────────────────────────────────────
ADMIN_USERNAME = "admin"

CATEGORY_WEIGHTS = {
    "Originalidade":      1.5,
    "Design":             1.2,
    "Utilidade":          1.0,
    "Projeto Codificado": 1.5,
    "Produto de Mercado": 1.3,
    "Viabilidade":        1.4,
    "Pitch":              1.1,
}

MAX_SCORE    = 5
TOTAL_WEIGHT = sum(CATEGORY_WEIGHTS.values())

# ── Models ────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    votes         = db.relationship("Vote", backref="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Team(db.Model):
    """Teams are created exclusively by the admin."""
    __tablename__ = "teams"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    votes      = db.relationship("Vote", backref="team_ref", lazy="dynamic",
                                 foreign_keys="Vote.team_name",
                                 primaryjoin="Team.name == Vote.team_name")


class Vote(db.Model):
    __tablename__ = "votes"

    id        = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), db.ForeignKey("teams.name"), nullable=False, index=True)
    category  = db.Column(db.String(80), nullable=False)
    score     = db.Column(db.Float, nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("team_name", "category", "user_id", name="uq_vote"),
    )


# ── DB init ───────────────────────────────────────────────────────────────────
ADMIN_PASSWORD = "Naruto123"

with app.app_context():
    db.create_all()

    # Ensure the admin account always exists with the correct password
    admin = User.query.filter_by(username=ADMIN_USERNAME).first()
    if admin:
        admin.set_password(ADMIN_PASSWORD)
    else:
        admin = User(username=ADMIN_USERNAME)
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
    db.session.commit()

# ── Helpers ───────────────────────────────────────────────────────────────────
def error(message: str, status: int = 400):
    return jsonify({"message": message}), status


def get_current_user() -> "User | None":
    return User.query.filter_by(username=get_jwt_identity()).first()


def require_admin(user: "User"):
    if user.username != ADMIN_USERNAME:
        return error("Acesso não autorizado.", 403)
    return None


# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return error("Usuário e senha são obrigatórios.")
    if len(username) < 3:
        return error("O usuário precisa ter pelo menos 3 caracteres.")
    if len(password) < 6:
        return error("A senha precisa ter pelo menos 6 caracteres.")
    if User.query.filter_by(username=username).first():
        return error("Este nome de usuário já está em uso.")

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Conta criada com sucesso."}), 201


@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return error("Usuário ou senha inválidos.", 401)

    token = create_access_token(identity=user.username)
    return jsonify({"token": token, "username": user.username}), 200


# ── Team management (admin only) ──────────────────────────────────────────────
@app.route("/teams", methods=["GET"])
def list_teams():
    """Public: return the list of registered teams."""
    teams = Team.query.order_by(Team.name).all()
    return jsonify([t.name for t in teams]), 200


@app.route("/teams", methods=["POST"])
@jwt_required()
def create_team():
    """Admin only: register a new team."""
    user   = get_current_user()
    denied = require_admin(user)
    if denied:
        return denied

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return error("O nome da equipe é obrigatório.")
    if len(name) > 100:
        return error("O nome da equipe pode ter no máximo 100 caracteres.")
    if Team.query.filter_by(name=name).first():
        return error("Já existe uma equipe com esse nome.")

    team = Team(name=name, created_by=user.id)
    db.session.add(team)
    db.session.commit()
    return jsonify({"message": f'Equipe "{name}" cadastrada com sucesso.', "name": name}), 201


@app.route("/teams/<string:team_name>", methods=["DELETE"])
@jwt_required()
def delete_team(team_name: str):
    """Admin only: delete a team and all its votes."""
    user   = get_current_user()
    denied = require_admin(user)
    if denied:
        return denied

    team = Team.query.filter_by(name=team_name).first()
    if not team:
        return error("Equipe não encontrada.", 404)

    Vote.query.filter_by(team_name=team_name).delete()
    db.session.delete(team)
    db.session.commit()
    return jsonify({"message": f'Equipe "{team_name}" excluída com sucesso.'}), 200


# ── Voting ────────────────────────────────────────────────────────────────────
@app.route("/vote", methods=["POST"])
@jwt_required()
def submit_vote():
    user = get_current_user()
    if not user:
        return error("Usuário não encontrado.", 404)

    data      = request.get_json(silent=True) or {}
    team_name = (data.get("teamName") or "").strip()
    votes     = data.get("votes") or {}

    if not team_name:
        return error("Selecione uma equipe.")
    if not votes:
        return error("Nenhum voto enviado.")

    # admin cannot vote
    if user.username == ADMIN_USERNAME:
        return error("O administrador não pode votar.", 403)

    # team must exist in the registry
    if not Team.query.filter_by(name=team_name).first():
        return error("Equipe não encontrada. Selecione uma equipe válida.")

    # validate scores
    for category, score in votes.items():
        if category not in CATEGORY_WEIGHTS:
            return error(f"Categoria inválida: {category}")
        if not isinstance(score, (int, float)) or not (1 <= score <= MAX_SCORE):
            return error(f"Nota inválida para '{category}'. Use valores de 1 a {MAX_SCORE}.")

    try:
        for category, score in votes.items():
            existing = Vote.query.filter_by(
                user_id=user.id, team_name=team_name, category=category
            ).first()
            if existing:
                existing.score = float(score)
            else:
                db.session.add(Vote(
                    team_name=team_name,
                    category=category,
                    score=float(score),
                    user_id=user.id,
                ))
        db.session.commit()
        return jsonify({"message": "Avaliação registrada com sucesso."}), 200
    except Exception as exc:
        db.session.rollback()
        return error(str(exc))


# ── Results ───────────────────────────────────────────────────────────────────
@app.route("/results", methods=["GET"])
def get_results():
    """Return ranked team results. Teams with no votes are included with 0."""
    all_teams = Team.query.all()
    all_votes  = Vote.query.all()

    # aggregate votes per team
    agg: dict[str, dict] = {t.name: {"categories": {}, "voters": set()} for t in all_teams}

    for vote in all_votes:
        if vote.team_name not in agg:
            continue
        agg[vote.team_name]["categories"].setdefault(vote.category, []).append(vote.score)
        agg[vote.team_name]["voters"].add(vote.user_id)

    results = []
    for team_name, data in agg.items():
        avg_scores: dict[str, float] = {}
        total_score: float = 0.0

        for category, scores in data["categories"].items():
            weight = CATEGORY_WEIGHTS.get(category, 1.0)
            avg    = sum(scores) / len(scores)
            pct    = (avg / MAX_SCORE * 100) * (weight / TOTAL_WEIGHT)
            avg_scores[category] = round(pct, 1)
            total_score += pct

        results.append({
            "teamName":   team_name,
            "scores":     avg_scores,
            "totalScore": round(min(total_score, 100.0), 1),
            "voterCount": len(data["voters"]),
        })

    results.sort(key=lambda x: x["totalScore"], reverse=True)
    return jsonify(results), 200


# ── Serve frontend ───────────────────────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # API routes are handled before this catch-all
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)