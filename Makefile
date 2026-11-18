
.PHONY:	venv install run debug clean lint 

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo ""
	@echo "Virtual environment created. Activate it with:"
	@echo "  source .venv/bin/activate"

run:
	python3 main.py map.txt

debug:
	python3 -m pdb main.py map.txt

lint:
	flake8 . --exclude=.venv
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs \
		--exclude '^\.venv'

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete