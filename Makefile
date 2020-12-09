# vim: noexpandtab filetype=make
help:
	@echo "make init		- Create venv and install requirements"
	@echo "make run			- Launch sensors' data collection"
	@echo "make test		- Launch tests"
	@echo "make checkstyle	- Run a checkstyle analysis"
	@echo "make postgres	- Run a postgres 12 container in foreground"
	@echo "make psql		- Run a psql console"

init:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

test:
	@./.venv/bin/python3 -m unittest discover -s tests -t . -v

checkstyle: pycodestyle pyflakes mypy

pycodestyle:
	@echo "Pycodestyle..."
	@.venv/bin/pycodestyle shcollector tests || true

pyflakes:
	@echo "Pyflakes..."
	@.venv/bin/pyflakes shcollector tests || true

mypy:
	@echo "mypy"
	@.venv/bin/mypy --strict shcollector/main.py || true

postgres:
	@docker run --rm \
	--name metrics-postgres \
	-e POSTGRES_PASSWORD=metrics \
	-e POSTGRES_USER=metrics \
	-e POSTGRES_DB=metrics \
	-p 5432:5432 \
	postgres:12

psql:
	@PGPASSWORD=metrics psql -h localhost metrics metrics

run:
	@.venv/bin/python3 smart-home-collector/main.py

debug:
	@.venv/bin/python3 smart-home-collector/main.py -d

simulator:
	@.venv/bin/python3 smart-home-collector/main.py -c tests/debug.ini

debug-simulator:
	@.venv/bin/python3 smart-home-collector/main.py -d -c tests/debug.ini

.PHONY: init test checkstyle postgres psql
