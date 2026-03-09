"""
FAESA Voting System — URL Configuration
All API routes are prefixed with /api/.
Static files (css, js) are served under /frontend/.
The catch-all at the end serves the frontend (index.html).
"""

from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.contrib.staticfiles.views import serve
from django.views.static import serve as static_serve

urlpatterns = [
    # API
    path("api/", include("api.urls")),

    # Serve frontend static files (styles.css, script.js, etc.)
    re_path(r"^frontend/(?P<path>.*)$", static_serve, {"document_root": settings.BASE_DIR / "frontend"}),

    # Frontend catch-all — must be last
    path("", TemplateView.as_view(template_name="index.html")),
    path("<path:path>", TemplateView.as_view(template_name="index.html")),
]