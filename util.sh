docker system prune -a

# update pip:
deactivate; rm -rf .pyenv; python3 -m virtualenv .pyenv; source .pyenv/bin/activate; pip install --upgrade pip; pip install -r requirements.update.txt; pip freeze > requirements.txt
