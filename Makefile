# Python interpreter used to create the virtual environment
PYTHON_VERSION ?= python3

# Virtual environment directory
VENV ?= .venv

# Python executable inside virtual environment
PYTHON ?= $(VENV)/bin/python

# Pip executable inside virtual environment
PIP ?= $(VENV)/bin/pip

# Census year to be processed
YEAR ?= $(shell date +%Y | awk '{print $$1 - 1}')

# Reset database before execution
RESET_DB ?= false

.PHONY: help venv install run clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv: ## Create Python virtual environment
	$(PYTHON_VERSION) -m venv $(VENV)

install: venv ## Install project dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run: ## Run the School Census pipeline (YEAR=2025 RESET_DB=true)
	@test -x $(PYTHON) || (echo "Virtual environment not found. Run: make install" && exit 1)
	$(PYTHON) -m src.main \
		--year $(YEAR) \
		$(if $(filter true,$(RESET_DB)),--reset-db,)

clean: ## Remove virtual environment and Python cache files
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +