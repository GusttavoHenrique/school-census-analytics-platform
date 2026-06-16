PYTHON_VERSION ?= python3
VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

# defining last year by default
ifndef YEAR
    YEAR := $(shell date +%Y | awk '{print $$1 - 1}')
endif

venv:
	$(PYTHON_VERSION) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) -m src.main --year $(YEAR)

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +