.SILENT :

build: clean coverage

lint:
	pylint *.py

test:
	python -m unittest discover -v

clean:

	rm -rf htmlcov

	# remove __pycache__ folders
	find . -name "__pycache__" -exec rm -rf {} +
	find tests/ -name "__pycache__" -exec rm -rf {} +

	# remove .pyc files
	find . -name "*.pyc" -exec rm {} +
	find tests/ -name "*.pyc" -exec rm {} +

coverage:
	coverage run -m unittest discover
	coverage html
