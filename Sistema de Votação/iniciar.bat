:: ═══════════════════════════════════════════
::  FAESA Voting System — Iniciar servidor
::  Execute este arquivo ou copie os comandos
::  no terminal dentro da pasta do projeto.
:: ═══════════════════════════════════════════

:: 1. Instalar dependências (só na primeira vez)
pip install -r requirements.txt

:: 2. Criar o banco de dados
python manage.py migrate

:: 3. Rodar o servidor
python manage.py runserver 0.0.0.0:8000