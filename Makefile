install:
	./setup.py install

test:
	python3 -m unittest src/bdc/tests.py

clean:
	rm -rf dist build bdc.egg-info
