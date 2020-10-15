.PHONY: deps mypy test zombies

WORLD_SIZE ?= auto

deps:
	pipenv install

dev-deps:
	pipenv install --dev

mypy: dev-deps
	pipenv run mypy --html-report mypy .

test: dev-deps mypy
	pipenv run pytest

zombies: deps
	WORLD_SIZE=$(WORLD_SIZE) pipenv run python3 -m cli
