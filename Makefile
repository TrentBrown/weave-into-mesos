help:
	python install.py --help

install-python-packages:
	pip install -r requirements.txt

download-weave-executable:
	curl -L git.io/weave -o ./weave
	sudo chmod a+x ./weave

setup: install-python-packages download-weave-executable

install:
	python install.py

all: setup install

.DEFAULT_GOAL := all
