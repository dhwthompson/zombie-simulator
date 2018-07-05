.PHONY: deps test watch zombies

WORLD_SIZE ?= auto

deps:
	pip install -q -r requirements.txt

test: deps
	pytest

watch: deps
	fswatch -or -e '.' -i '\.py$$' . | xargs -I {} -L 1 pytest -q

zombies: deps
	WORLD_SIZE=$(WORLD_SIZE) python3 -m cli
