.PHONY: deps mypy test zombies

WORLD_SIZE ?= auto

deps:
	pip install -q -r requirements.txt

mypy:
	mypy --html-report mypy .

test: mypy
	pytest

zombies: deps
	WORLD_SIZE=$(WORLD_SIZE) python3 -m cli
