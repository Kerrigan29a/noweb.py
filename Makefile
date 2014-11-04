all: noweb.py README.md

# Builds to a temporary file first, then rebuilds using the temporary as script to ensure we don't accidentily break our buildscript
noweb.py: noweb.py.nw
	@tmpfile=`mktemp /tmp/noweb.XXXXXXXXXX 2>/dev/null || mktemp -t noweb` ; \
	set -x ; \
	./bootstrap.py -o $$tmpfile -R $@ $< && \
	python $$tmpfile -o $@ tangle -R $@ $< && \
	chmod +x $@ ; \
	r=$$? ; \
	rm $$tmpfile ; \
	exit $$r

README.md: noweb.py.nw noweb.py
	./noweb.py -o $@ weave --default-code-syntax=python $<

clean:
	-rm noweb.py
	-rm README.md
	-rm *.pyc
	-rm -r build
