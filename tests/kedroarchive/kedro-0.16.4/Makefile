install: build-docs
	rm -rf kedro/framework/html
	cp -r docs/build/html kedro/framework
	pip install .

clean:
	rm -rf build dist docs/build kedro/html pip-wheel-metadata .mypy_cache .pytest_cache features/steps/test_plugin/test_plugin.egg-info
	find . -regex ".*/__pycache__" -exec rm -rf {} +
	find . -regex ".*\.egg-info" -exec rm -rf {} +
	pre-commit clean || true

install-pip-setuptools:
	python -m pip install -U "pip>=20.0,<20.2" "setuptools>=38.0" wheel

legal:
	python tools/license_and_headers.py

lint:
	pre-commit run -a --hook-stage manual

test:
	pytest tests --cov-config pyproject.toml

test-no-spark:
	pytest tests --cov-config pyproject_no_spark.toml --ignore tests/extras/datasets/spark

e2e-tests:
	behave

pip-compile:
	pip-compile -q -o -

secret-scan:
	trufflehog --max_depth 1 --exclude_paths trufflehog-ignore.txt .

SPHINXPROJ = Kedro

build-docs:
	./docs/build-docs.sh

devserver: build-docs
	cd docs && npm install && npm start

package: clean install
	python setup.py sdist bdist_wheel

install-test-requirements:
	pip install -r test_requirements.txt

install-pre-commit: install-test-requirements
	pre-commit install --install-hooks

uninstall-pre-commit:
	pre-commit uninstall
	pre-commit uninstall --hook-type pre-push

print-python-env:
	@./tools/print_env.sh
