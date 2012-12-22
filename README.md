This executable document first appeared as a blog post on
http://jonaquino.blogspot.com/2010/04/nowebpy-or-worlds-first-executable-blog.html


###### License

```python
# Copyright (c) 2010  Jonathan Aquino (jonathan.aquino@gmail.com)
# Copyright (c) 2012  Giel van Schijndel (me@mortis.eu)
```


I have recently been interested in the old idea of
[literate programming](http://en.wikipedia.org/wiki/Literate_programming).
Basically, you have a document that describes in detail how a program works, and
it has embedded chunks of code. It allows you to see the thoughts of the programmer
as he explains how he writes the program using prose. A tool is provided that you
can use to extract the working program from chunks of code in the document.

Here's the thing: *what you are reading right now is a literate program*.

Yes, you can copy this blog post into a file and feed it into the tool, and it
will spit out a program. Q: Where do I get the tool? A: That's the program that
this document spits out. This document will produce a script that you can use to
extract code from [noweb](http://en.wikipedia.org/wiki/Noweb)-format literate programs.

Why do we need to make a new tool if the [noweb](http://en.wikipedia.org/wiki/Noweb)
tool already exists? Because the noweb tool is hard to install. It's not super-hard,
but most people don't want to spend time trying to compile it from source. There
are Windows binaries but you have to [get](http://web.archive.org/web/*/http://www.literateprogramming.com/noweb/nowebinstall.html)
them from the Wayback Machine.

Anyway, the noweb tool doesn't seem to do very much, so why not write a little
script to emulate it?

And that is what we will do now.









# DOWNLOAD

If you are just interested in the noweb.py script produced by this document,
you can [download](http://github.com/JonathanAquino/noweb.py/raw/master/noweb.py) it from GitHub.









# USAGE

The end goal is to produce a Python script that will take a literate program
as input (noweb format) and extract code from it as output. For example,

    noweb.py -Rhello.php hello.noweb -o hello.php

This will read in a file called hello.noweb and extract the code labelled "hello.php".
We redirect the output into a hello.php file.

# DEFINING THE READER

In order to allow processing of multiple literate documents from the same program we wrap all parsing and
code-generating functionaility in a single class.


###### Defining the processor

```python
class NowebReader(object):
    <<Defining the syntax>>

    def __init__(self, file=None):
        self.chunks = {None: []}

        if file is not None:
            self.read(file)

    def read(self, file):
        if isinstance(file, basestring):
            infile = open(file)
        else:
            infile = file
        try:
            <<Reading in the file>>
        finally:
            if isinstance(file, basestring):
                infile.close()

    def expand(self, chunkName, indent="", weave=False, github_syntax=None):
        <<Recursively expanding the output chunk>>

    def write(self, chunkName, file=None, weave=False, github_syntax=None):
        if isinstance(file, basestring) or file is None:
            outfile = StringIO()
        else:
            outfile = file

        <<Outputting the chunks>>

        if file is None:
            return outfile.getvalue()
        elif isinstance(file, basestring):
            with open(file, 'w') as f:
                f.write(outfile.getvalue())
```







# READING IN THE FILE

In a literate program, there are named chunks of code interspersed throughout
the document. Take the chunk of code below. The name of it is "Reading in the file".
The chunk ends with a line starting with an @ sign.

First we begin with syntax definitions of regexes matching the start, end and invocations
of a chunk. Important to note is that the @ sign only ends a chunk only if it is followed
by whitespace or is the last symbol on the line. Additionally a double @@ in the first
column of a line that is immediately followed by whitespace or is the end of the line is
replaced with a single @ and does *not* terminate the chunk. This is intended as an
escaping technique allowing the use of the @ sign on the first column for languages that
require it for their own syntax.


###### Defining the syntax

```python
chunk_re         = re.compile(r'<<(?P<name>[^>]+)>>')
chunk_def        = re.compile(chunk_re.pattern + r'=')
chunk_at         = re.compile(r'^@@(?=\s|$)')
chunk_end        = re.compile(r'^@(?:\s(?P<text>.*))?$', re.DOTALL)
chunk_invocation = re.compile(r'^(?P<indent>\s*)' + chunk_re.pattern + r'\s*$')
```


Let's start by reading in the file given on the command line. We'll build up
a map called "chunks", which will contain the chunk names and the lines of each chunk.


###### Reading in the file

```python
chunkName = None

for lnum, line in enumerate(infile):
    match = self.chunk_def.match(line)
    if match and not chunkName:
        self.chunks[chunkName].append((lnum + 1, [match.group('name')]))
        chunkName = match.group('name')
        self.chunks[chunkName] = []
    else:
        match = self.chunk_end.match(line)
        if match:
            chunkName = None
            text = match.group('text')
            if text:
                try:
                    self.chunks[chunkName][-1][-1].append((lnum + 1, text))
                except (IndexError, AttributeError):
                    pass
        else:
            line = self.chunk_at.sub('@', line)
            self.chunks[chunkName].append((lnum + 1, line))
```










# PARSING THE COMMAND-LINE ARGUMENTS

Now that we have a map of chunk names to the lines of each chunk, we need to know
which chunk name the user has asked to extract. In other words, we need to parse
the command-line arguments given to the script:

    noweb.py -Rhello.php hello.noweb


###### Defining the command-line parser

```python
cmd_line_parser = argparse.ArgumentParser('NoWeb command line options.')
cmd_line_parser.add_argument('infile',         metavar='FILE',              help='input file to process, "-" for stdin')
cmd_line_parser.add_argument('-o', '--output', metavar='FILE', default='-', help='file to output to, "-" for stdout')

#FIXME: Apparently Python doesn't want groups within groups?
#_output_mode_dependent = cmd_line_parser.add_mutually_exclusive_group(required=True)
_output_mode_dependent = cmd_line_parser

_tangle_options = _output_mode_dependent.add_argument_group('tangle', 'Tangle options')
_tangle_options.add_argument('-R', '--chunk', metavar='CHUNK',    help='name of chunk to write to stdout')

_weave_options  = _output_mode_dependent.add_argument_group('weave',  'Weave options')
_weave_options.add_argument('-w', '--weave', action='store_true', help='weave output instead of tangling')
_weave_options.add_argument('--github-syntax', metavar='LANGUAGE', help='use GitHub-Flavoured MarkDown as output for chunks')
```



###### Parsing the command-line arguments

```python
args = cmd_line_parser.parse_args()

if args.infile == '-':
    infile = sys.stdin
else:
    infile = open(args.infile, 'r')
```










# RECURSIVELY EXPANDING THE OUTPUT CHUNK

So far, so good. Now we need a recursive function to expand any chunks found
in the output chunk requested by the user. Take a deep breath.


###### Recursively expanding the output chunk

```python
for lnum, line in self.chunks[chunkName]:
    if isinstance(line, basestring):
        match = self.chunk_invocation.match(line)
    else:
        match = None
    if match:
        for lnum, line in self.expand(match.group('name'), indent + match.group('indent'), weave):
            yield lnum, line
    else:
        if isinstance(line, list) and weave:
            <<Weave chunks>>
        else:
            # Only add indentation to non-empty lines
            if line and line != '\n':
                line = indent + line
            yield lnum, line
```


When weaving chunks need to be written using Markdown code-block syntax. This either means
indenting the block with 4 spaces. Alternatively when GitHub-flavoured Markdown is chosen
to get language-specific syntax-highlighting we wrap the block in markers and mention the
language to use for highlighting.


###### Weave chunks

```python
# Add a heading with the chunk's name.
yield lnum, '\n'
yield lnum, '###### %s\n' % tuple(line[:1])
yield lnum, '\n'

if github_syntax:
    yield lnum, '```%s\n' % (github_syntax,)

for def_lnum, def_line in self.chunks[line[0]]:
    if not github_syntax:
        def_line = '    ' + def_line
    yield def_lnum, def_line

if github_syntax:
    yield lnum, '```\n'
# Following text or separating new-line
try:
    yield line[1][0], line[1][1]
except IndexError:
    yield lnum, '\n'
```









# OUTPUTTING THE CHUNKS

The last step is easy. We just call the recursive function and output the result.


###### Outputting the chunks

```python
for _, line in self.expand(chunkName, weave=weave, github_syntax=github_syntax):
    outfile.write(line)
```

And we're done. We now have a tool to extract code from a literate programming document.
Try it on this blog post!










# APPENDIX I: GENERATING THE SCRIPT

To generate noweb.py from this document, you first need a tool to extract the
code from it. You can use the original [noweb](http://www.cs.tufts.edu/~nr/noweb/)
tool, but that's a bit cumbersome to install, so it's easier to use the
Python script [noweb.py](http://github.com/JonathanAquino/noweb.py/raw/master/noweb.py).

Then you can generate noweb.py from noweb.py.nw as follows:

    noweb.py -Rnoweb.py noweb.py.nw -o noweb.py










# APPENDIX II: SUMMARY OF THE PROGRAM

Here's how the pieces we have discussed fit together:


###### noweb.py

```python
#!/usr/bin/env python

<<License>>

"""
This program extracts code from a literate programming document in "noweb"
format.  It was generated from noweb.py.nw, itself a literate programming
document.
"""

import argparse
import re
import sys
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

<<Defining the command-line parser>>
<<Defining the processor>>

def main():
    <<Parsing the command-line arguments>>
    doc = NowebReader()
    doc.read(infile)
    out = args.output
    if out == '-':
        out = sys.stdout
    doc.write(args.chunk, out, weave=args.weave, github_syntax=args.github_syntax)

if __name__ == "__main__":
    main()
```

