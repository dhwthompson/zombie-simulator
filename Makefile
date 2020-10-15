.PHONY: deps mypy test zombies

WORLD_SIZE ?= auto

deps:
	pipenv install

dev-deps:
	pipenv install --dev

mypy:
	pipenv run mypy --html-report mypy .

test:
	pipenv run pytest

test-all: mypy test

zombies: deps
	WORLD_SIZE=$(WORLD_SIZE) pipenv run python3 -m cli
