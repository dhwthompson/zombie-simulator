.PHONY: deps mypy test zombies

WORLD_SIZE ?= auto

deps:
	pipenv install

dev-deps:
	pipenv install --dev

mypy: dev-deps
	mypy --html-report mypy .

test: dev-deps mypy
	pytest

zombies: deps
	WORLD_SIZE=$(WORLD_SIZE) python3 -m cli
