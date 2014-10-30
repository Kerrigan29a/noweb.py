all: noweb.py README.md

# Builds to a temporary file first, then rebuilds using the temporary as script to ensure we don't accidentily break our buildscript
noweb.py: noweb.py.nw
	@tmpfile=`mktemp /tmp/noweb.XXXXXXXXXX 2>/dev/null || mktemp -t noweb` ; \
	set -x ; \
	./bootstrap_noweb.py -R $@ $< -o $$tmpfile && \
	python $$tmpfile -R $@ $< -o $@ && \
	chmod +x $@ ; \
	r=$$? ; \
	rm $$tmpfile ; \
	exit $$r

README.md: noweb.py.nw noweb.py
	./noweb.py -w $< -o $@ --default-code-syntax=python

clean:
	-rm noweb.py
	-rm README.md
