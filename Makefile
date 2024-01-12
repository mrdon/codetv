.PHONY: run tunnel client help venv format run


# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv: ## Create python venv
	python3.12 -m venv venv
	venv/bin/pip install --upgrade pip-tools pip
	venv/bin/pip-compile
	venv/bin/pip install -r requirements.txt
	
format: ## Format the code
	venv/bin/black codetv
	venv/bin/reorder-python-imports --py38-plus `find codetv -name "*.py"` || venv/bin/black codetv --target-version py38


run: ## Run the app locally
#	docker-compose kill
#	docker-compose up -d
#	bin/set-from-env.sh
	venv/bin/hypercorn --reload -b localhost:8090 codetv.web:app

