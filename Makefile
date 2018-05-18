.PHONY: deps test zombies

deps:
	pip install -q -r requirements-dev.txt

test: deps
	pytest

zombies:
	python3 -m cli
