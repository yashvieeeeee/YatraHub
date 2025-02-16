@echo off
mkdir flask_project
cd flask_project

mkdir static templates instance
type nul > run.py
type nul > config.py
type nul > requirements.txt
type nul > .gitignore

cd static
mkdir css js img
cd..

cd templates
type nul > base.html
type nul > index.html
cd..

echo Flask > requirements.txt
echo python-dotenv >> requirements.txt

echo venv/ >> .gitignore
echo __pycache__/ >> .gitignore
echo instance/ >> .gitignore
echo .env >> .gitignore

echo Created Flask project structure successfully!
pause