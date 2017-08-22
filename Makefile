.POSIX:
.SUFFIXES:

.SILENT :

PYTHON = python
PYLINT = pylint
COVERAGE = coverage

#
# sphinx
#

SPHINXOPTS    =
SPHINXBUILD   = python -msphinx
SPHINXAPIDOC  = sphinx-apidoc
BUILDDIR      = doc/_build
APIDIR		  = doc/api

ALLSPHINXOPTS   = -d $(BUILDDIR)/.doctrees $(SPHINXOPTS) doc/

#
# targets
#

all: dist

.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  all        to build the entire project (default)"
	@echo "  clean      remove all generated build artifacts"
	@echo "  doc        to make standalone HTML documentation files"

dist: clean build test doc
	#TODO build documentation
	#TODO create release
	echo .

build: clean coverage

lint:
	$(PYLINT) *.py

sanity:
	$(PYTHON) -m unittest discover -v --failfast

test:
	$(PYTHON) -m unittest discover -v

clean:

	rm -rf htmlcov

	# remove __pycache__ folders
	find . -name "__pycache__" -exec rm -rf {} +
	find tests/ -name "__pycache__" -exec rm -rf {} +

	# remove .pyc files
	find . -name "*.pyc" -exec rm {} +
	find tests/ -name "*.pyc" -exec rm {} +

	# remove documentation build artifacts
	rm -rf $(BUILDDIR)/*

coverage:
	$(COVERAGE) run -m unittest discover
	$(COVERAGE) html

api_doc:
	@echo "Refreshing API documents."
	$(SPHINXAPIDOC) -o $(APIDIR) ..
	rm $(APIDIR)/modules.rst
	@echo
	@echo "Finished refreshing API."

doc: api_doc
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."
