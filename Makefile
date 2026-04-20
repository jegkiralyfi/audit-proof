.PHONY: run-api run-web test lint

run-api:
	python apps/api/main.py

run-web:
	python apps/web/app.py

test:
	pytest
