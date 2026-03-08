"""
FAESA Voting System — Views (API endpoints)
"""

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import IntegrityError

import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Team, Vote

# ── Constants ─────────────────────────────────────────────────────────────────
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Naruto123"

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


# ── Helpers ───────────────────────────────────────────────────────────────────
def err(message: str, code: int = 400):
    return Response({"message": message}, status=code)


def get_user_from_request(request) -> "User | None":
    """request.user is already our custom User model via UsernameJWTAuthentication."""
    user = getattr(request, "user", None)
    if isinstance(user, User):
        return user
    return None


def make_token(user: User) -> str:
    """Generate a JWT access token string for the given user."""
    refresh = RefreshToken()
    refresh["username"] = user.username
    # Also set user_id so simplejwt does not reject the token
    refresh.access_token["username"] = user.username
    return str(refresh.access_token)


# ── Auth ──────────────────────────────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data     = request.data
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return err("Usuário e senha são obrigatórios.")
        if len(username) < 3:
            return err("O usuário precisa ter pelo menos 3 caracteres.")
        if len(password) < 6:
            return err("A senha precisa ter pelo menos 6 caracteres.")
        if User.objects.filter(username=username).exists():
            return err("Este nome de usuário já está em uso.")

        user = User(username=username)
        user.set_password(password)
        user.save()

        return Response({"message": "Conta criada com sucesso."}, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data     = request.data
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return err("Usuário ou senha inválidos.", 401)

        if not user.check_password(password):
            return err("Usuário ou senha inválidos.", 401)

        token = make_token(user)
        return Response({"token": token, "username": user.username})


# ── Teams ─────────────────────────────────────────────────────────────────────
class TeamsView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        """Public: list all team names."""
        teams = Team.objects.order_by("name").values_list("name", flat=True)
        return Response(list(teams))

    def post(self, request):
        """Admin only: create a team."""
        user = get_user_from_request(request)
        if not user:
            return err("Usuário não encontrado.", 404)
        if user.username != ADMIN_USERNAME:
            return err("Acesso não autorizado.", 403)

        name = (request.data.get("name") or "").strip()
        if not name:
            return err("O nome da equipe é obrigatório.")
        if len(name) > 100:
            return err("O nome pode ter no máximo 100 caracteres.")
        if Team.objects.filter(name=name).exists():
            return err("Já existe uma equipe com esse nome.")

        Team.objects.create(name=name, created_by=user)
        return Response(
            {"message": f'Equipe "{name}" cadastrada com sucesso.', "name": name},
            status=201
        )


class TeamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, team_name):
        """Admin only: delete a team and all its votes."""
        user = get_user_from_request(request)
        if not user:
            return err("Usuário não encontrado.", 404)
        if user.username != ADMIN_USERNAME:
            return err("Acesso não autorizado.", 403)

        try:
            team = Team.objects.get(name=team_name)
        except Team.DoesNotExist:
            return err("Equipe não encontrada.", 404)

        Vote.objects.filter(team_name=team_name).delete()
        team.delete()
        return Response({"message": f'Equipe "{team_name}" excluída com sucesso.'})


# ── Voting ────────────────────────────────────────────────────────────────────
class VoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return err("Usuário não encontrado.", 404)

        if user.username == ADMIN_USERNAME:
            return err("O administrador não pode votar.", 403)

        data      = request.data
        team_name = (data.get("teamName") or "").strip()
        votes     = data.get("votes") or {}

        if not team_name:
            return err("Selecione uma equipe.")

        if not votes:
            return err("Nenhum voto enviado.")

        if not Team.objects.filter(name=team_name).exists():
            return err("Equipe não encontrada. Selecione uma equipe válida.")

        # 🚫 Impede votar duas vezes na mesma equipe
        if Vote.objects.filter(user=user, team_name=team_name).exists():
            return err("Você já votou nesta equipe.")

        # valida categorias e notas
        for category, score in votes.items():
            if category not in CATEGORY_WEIGHTS:
                return err(f"Categoria inválida: {category}")

            if not isinstance(score, (int, float)) or not (1 <= score <= MAX_SCORE):
                return err(f"Nota inválida para '{category}'. Use valores de 1 a {MAX_SCORE}.")

        try:
            # salva votos
            for category, score in votes.items():
                Vote.objects.create(
                    user=user,
                    team_name=team_name,
                    category=category,
                    score=float(score),
                )

            return Response({"message": "Avaliação registrada com sucesso."})

        except Exception as exc:
            return err(str(exc))

# ── Results ───────────────────────────────────────────────────────────────────
class ResultsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        all_teams = Team.objects.all()
        all_votes = Vote.objects.select_related("user").all()

        # aggregate
        agg = {t.name: {"categories": {}, "voters": set()} for t in all_teams}

        for vote in all_votes:
            if vote.team_name not in agg:
                continue
            agg[vote.team_name]["categories"].setdefault(vote.category, []).append(vote.score)
            agg[vote.team_name]["voters"].add(vote.user_id)

        results = []
        for team_name, data in agg.items():
            avg_scores   = {}
            total_score  = 0.0

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
        return Response(results)


# ── Health ────────────────────────────────────────────────────────────────────
class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})