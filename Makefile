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
	@echo "Not implemented yet"

checkstyle: pycodestyle pyflakes

pycodestyle:
	@echo "Pycodestyle..."
	@.venv/bin/pycodestyle smart-home-collector/*.py || true

pyflakes:
	@echo "Pyflakes..."
	@.venv/bin/pyflakes smart-home-collector/*.py || true

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

.PHONY: init test checkstyle postgres psql
