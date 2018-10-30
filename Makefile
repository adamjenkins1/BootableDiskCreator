install:
	./setup.py install

test:
	python3 -m unittest src/bdc/tests.py
