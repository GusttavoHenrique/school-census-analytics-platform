PYTHON_VERSION ?= python3
VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

YEAR ?= $(shell date +%Y | awk '{print $$1 - 1}')

venv:
	$(PYTHON_VERSION) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	@test -x $(PYTHON) || (echo "Virtual environment not found. Run: make install" && exit 1)
	$(PYTHON) -m src.main --year $(YEAR)

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +