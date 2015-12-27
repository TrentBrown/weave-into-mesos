help:
	python install.py --help

install-python-packages:
	pip install -r requirements.txt

download-weave-executable:
	curl -L git.io/weave -o ./weave
	sudo chmod a+x ./weave

download-weave-scope-executable:
	curl -L https://github.com/weaveworks/scope/releases/download/latest_release/scope -o ./weave-scope
	sudo chmod a+x ./weave-scope

setup: install-python-packages download-weave-executable download-weave-scope-executable

install:
	python install.py

all: setup install

.DEFAULT_GOAL := all
