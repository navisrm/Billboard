# Override on the command line, e.g. `make deploy PI=navisrm@naveen-pi5.local`
PI       ?= navisrm@naveen-pi5.local
APP_DIR  ?= Billboard
REPO     ?= https://github.com/navisrm/Billboard.git
BRANCH   ?= main
MSG      ?= Update billboard

.PHONY: help run push deploy env status logs restart reboot ssh

help:
	@echo "make run                     Run locally on this machine"
	@echo "make push MSG=\"...\"          Commit all changes and push to GitHub"
	@echo "make deploy                  Push, then pull + install + restart on the Pi"
	@echo "make env                     Copy local .env to the Pi"
	@echo "make status | logs | restart Manage the service on the Pi"
	@echo "make reboot                  Reboot the Pi (reloads the kiosk browser too)"
	@echo "make ssh                     Open a shell on the Pi"

run:
	venv/bin/python app.py

push:
	git add -A
	git diff --cached --quiet || git commit -m "$(MSG)"
	git push origin $(BRANCH)

deploy: push
	ssh $(PI) 'if [ -d $(APP_DIR)/.git ]; then git -C $(APP_DIR) pull --ff-only origin $(BRANCH); else git clone -b $(BRANCH) $(REPO) $(APP_DIR); fi'
	@if [ -f .env ]; then $(MAKE) env; fi
	ssh -t $(PI) 'bash $(APP_DIR)/deploy/install.sh'

env:
	scp .env $(PI):$(APP_DIR)/.env

status:
	ssh $(PI) 'systemctl --no-pager status billboard.service'

logs:
	ssh -t $(PI) 'journalctl -u billboard.service -f'

restart:
	ssh -t $(PI) 'sudo systemctl restart billboard.service'

reboot:
	ssh -t $(PI) 'sudo reboot'

ssh:
	ssh $(PI)
