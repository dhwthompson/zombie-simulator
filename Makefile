.PHONY: deps test zombies

WORLD_SIZE ?= auto

deps:
	pip install -q -r requirements-dev.txt

test: deps
	pytest

zombies:
	WORLD_SIZE=$(WORLD_SIZE) python3 -m cli
