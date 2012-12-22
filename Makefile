all: noweb.py README.md

# Builds to a temporary file first, then rebuilds using the temporary as script to ensure we don't accidentily break our buildscript
noweb.py: noweb.py.nw
	@tmpfile=`mktemp` ; \
	set -x ; \
	./noweb.py -R $@ $< -o $$tmpfile && \
	python $$tmpfile -R $@ $< -o $@ && \
	r=$$? ; \
	rm $$tmpfile ; \
	exit $$r

README.md: noweb.py.nw noweb.py
	./noweb.py -w $< -o $@ --github-syntax=python
