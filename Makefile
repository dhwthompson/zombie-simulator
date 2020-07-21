.PHONY: deps mypy test watch zombies

WORLD_SIZE ?= auto

deps:
	pip install -q -r requirements.txt

mypy:
	mypy --html-report mypy .

test: mypy
	pytest

watch: deps
	fswatch -or -e '.' -i '\.py$$' . | xargs -I {} -L 1 pytest -q --ff -x

zombies: deps
	WORLD_SIZE=$(WORLD_SIZE) python3 -m cli
