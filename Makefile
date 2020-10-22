.PHONY: deps flame mypy test zombies

WORLD_SIZE ?= auto

deps:
	pipenv install

dev-deps:
	pipenv install --dev

lint:
	pipenv run black --check .

mypy:
	pipenv run mypy --html-report mypy .

flame:
	sudo TICK=0 MAX_AGE=100 WORLD_SIZE=$(WORLD_SIZE) py-spy record -o flame.svg -- python -m cli

test:
	pipenv run pytest

test-all: lint mypy test

zombies: deps
	WORLD_SIZE=$(WORLD_SIZE) pipenv run python3 -m cli
