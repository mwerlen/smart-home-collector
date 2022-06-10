# vim: noexpandtab filetype=make
help:
	@echo "make init			- Create venv and install requirements"
	@echo "make run				- Launch sensors' data collection"
	@echo "make debug			- Launch sensors' data collection with debug logs"
	@echo "make simulator		- Launch sensors' data collection in simulation mode"
	@echo "make debug-simulator	- Launch sensors' data collection in simulation mode with debug logs"
	@echo "make test			- Launch tests"
	@echo "make checkstyle		- Run a checkstyle analysis"
	@echo "make postgres		- Run a postgres 12 container in foreground"
	@echo "make psql			- Run a psql console"

init:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/mypy --install-types

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
	@.venv/bin/python3 shcollector/main.py

debug:
	@.venv/bin/python3 shcollector/main.py -d

simulator:
	@.venv/bin/python3 shcollector/main.py -c tests/debug.ini

debug-simulator:
	@.venv/bin/python3 shcollector/main.py -d -c tests/debug.ini

.PHONY: init test checkstyle postgres psql
