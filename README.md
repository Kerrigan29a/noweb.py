
# Noweb.py
[![Build Status](https://travis-ci.org/Kerrigan29a/noweb.py.svg?branch=master)](https://travis-ci.org/Kerrigan29a/noweb.py)



# Syntax highlighting
If you use [Atom](https://atom.io/), you can install the
[literate package](https://atom.io/packages/language-literate) also created by
me.



# TODO
- [ ] Rewrite the documentation to reflect the new changes.
- [ ] Change/Delete [Download](#download)
- [ ] Change/Delete [Appendix I](#appendix-i-generating-the-script)

---

This executable document first appeared as a blog post on
http://jonaquino.blogspot.com/2010/04/nowebpy-or-worlds-first-executable-blog.html


###### License

```python
# Copyright (c) 2010  Jonathan Aquino (jonathan.aquino@gmail.com)
# Copyright (c) 2012  Giel van Schijndel (me@mortis.eu)
# Copyright (c) 2014  Javier Escalada Gómez (kerrigan29a@gmail.com)
```

I have recently been interested in the old idea of
[literate programming](http://en.wikipedia.org/wiki/Literate_programming).
Basically, you have a document that describes in detail how a program works,
and it has embedded chunks of code. It allows you to see the thoughts of the
programmer as he explains how he writes the program using prose. A tool is
provided that you can use to extract the working program from chunks of code in
the document.

Here's the thing: *what you are reading right now is a literate program*.

Yes, you can copy this blog post into a file and feed it into the tool, and it
will spit out a program. Q: Where do I get the tool? A: That's the program that
this document spits out. This document will produce a script that you can use to
extract code from [noweb](http://en.wikipedia.org/wiki/Noweb)-format literate
programs.

Why do we need to make a new tool if the
[noweb](http://en.wikipedia.org/wiki/Noweb) tool already exists? Because the
noweb tool is hard to install. It's notsuper-hard, but most people don't want to
spend time trying to compile it from source. There are Windows binaries but
you have to
[get](http://web.archive.org/web/*/http://www.literateprogramming.com/noweb/nowebinstall.html)
them from the Wayback Machine.

Anyway, the noweb tool doesn't seem to do very much, so why not write a little
script to emulate it?

And that is what we will do now.



# DOWNLOAD

If you are just interested in the noweb.py script produced by this document,
you can
[download](http://github.com/JonathanAquino/noweb.py/raw/master/noweb.py)
it from GitHub.



# USAGE

The end goal is to produce a Python script that will take a literate program
as input (noweb format) and extract code from it as output. For example,

    noweb.py -Rhello.php hello.noweb -o hello.php

This will read in a file called hello.noweb and extract the code labelled
"hello.php". We redirect the output into a hello.php file.



# DEFINING THE READER

In order to allow processing of multiple literate documents from the same
program we wrap all parsing and code-generating functionaility in a single
class.


###### Defining the processor

```python
Chunk = collections.namedtuple("Chunk",
    ["syntax", "lines", "position"])



class Line(collections.namedtuple("Line",
    ["type", "value", "indentation", "position"])):
    __slots__ = ()

    DOCUMENTATION = 1
    CHUNK_BEGIN = 2
    CODE = 3
    REFERENCE = 4
    CHUNK_END = 5

    def __str__(self):
        return "".join([self.indentation, self.value])


class Reader(object):
    <<Defining the syntax>>

    def __init__(self, file=None, encoding=None):
        # Section with key None is the documentation section
        self.chunks = {None: Chunk(syntax="text", lines=[], position=0)}
        self.last_fname = None
        self.encoding = encoding

        if file is not None:
            self.read(file)

    def read(self, file):
        if isinstance(file, basestring):
            input = open(file)
            self.last_fname = file
        else:
            input = file
            self.last_fname = None
        try:
            <<Reading in the file>>
        finally:
            if isinstance(file, basestring):
                input.close()

    def _indent_line(self, line, indent):
        return line if line.value in ('', '\n', '\r\n') \
            else line._replace(indentation=indent + line.indentation)

    <<Tangle chunks>>

    <<Weave chunks>>

    <<Format chunks>>

    def write(self, lines, file=None):
        if isinstance(file, basestring) or file is None:
            outfile = StringIO()
        else:
            outfile = file

        <<Outputting the chunks>>

        if file is None:
            return outfile.getvalue()
        elif isinstance(file, basestring):
            with open(file, 'w') as f:
                txt = outfile.getvalue()
                if isinstance(txt, unicode):
                    txt = txt.encode(self.encoding)
                f.write(txt)
```



# READING IN THE FILE

In a literate program, there are named chunks of code interspersed throughout
the document. Take the chunk of code below. The name of it is
"Reading in the file". The chunk ends with a line starting with an @ sign.

First we begin with syntax definitions of regexes matching the start, end and
invocations of a chunk. Important to note is that the @ sign only ends a chunk
only if it is followed by whitespace or is the last symbol on the line.
Additionally a double @@ in the first column of a line that is immediately
followed by whitespace or is the end of the line is replaced with a single @ and
does *not* terminate the chunk. This is intended as anescaping technique
allowing the use of the @ sign on the first column for languages that require it
for their own syntax.


###### Defining the syntax

```python
chunk_re         = re.compile(r'<<(?:(?P<syntax>[^:]+):)?(?P<name>[^>]+)>>')
chunk_def        = re.compile(chunk_re.pattern + r'=')
chunk_at         = re.compile(r'^@@(?=\s|$)')
chunk_end        = re.compile(r'^@(?:\s(?P<text>.*))?$', re.DOTALL)
chunk_invocation = re.compile(r'^(?P<indent>\s*)' + chunk_re.pattern + r'\s*$')
firstline_re     = re.compile(r'^\s*.*\s*literate:\s*(?:'
    + r'(?:syntax\s*=\s*(?P<syntax>[a-zA-Z0-9_-]*))|'
    + r'(?:encoding\s*=\s*(?P<encoding>[a-zA-Z0-9_-]*))|'
    + r'\s*'
    + r')*.*\s*$')
```

Let's start by reading in the file given on the command line. We'll build up
a map called "chunks", which will contain the chunk names and the lines of each
chunk.


###### Reading in the file

```python
chunkName = None

for lnum, line in enumerate(input):
    if self.encoding:
        line = line.decode(self.encoding)
    if lnum == 0:
        match = self.firstline_re.match(line)
        if match:
            options = match.groupdict()
            encoding = options["encoding"]
            if encoding:
                self.encoding = encoding
            syntax = options["syntax"]
            if syntax:
                self.chunks[None] = self.chunks[None]._replace(syntax=syntax)
            continue
    match = self.chunk_def.match(line)
    if match and not chunkName:
        chunkName = match.group('name')
        chunkSyntax = match.group('syntax')
        # Append reference to code in documentation
        self.chunks[None].lines.append(Line(type=Line.CHUNK_BEGIN,
            value=chunkName, indentation="", position=lnum + 1))
        # Store code chunk
        self.chunks[chunkName] = Chunk(syntax=chunkSyntax, lines=[],
            position=lnum + 1)
    else:
        match = self.chunk_end.match(line)
        if match:
            chunkName = None
            text = match.group('text')
            if text:
                self.chunks[chunkName].lines.append(Line(
                    type=Line.DOCUMENTATION,
                    value=text, indentation="", position=lnum + 1))
        else:
            line = self.chunk_at.sub('@', line)
            match = self.chunk_invocation.match(line)
            if match:
                sub_chunk = match.group('name')
                sub_indent = match.group('indent')
                self.chunks[chunkName].lines.append(Line(type=Line.REFERENCE,
                    value=sub_chunk, indentation=sub_indent, position=lnum + 1))
            else:
                self.chunks[chunkName].lines.append(Line(
                    type=Line.CODE if chunkName else Line.DOCUMENTATION,
                    value=line, indentation="", position=lnum + 1))
```



# PARSING THE COMMAND-LINE ARGUMENTS

Now that we have a map of chunk names to the lines of each chunk, we need to
know which chunk name the user has asked to extract. In other words, we need to
parse the command-line arguments given to the script:

    noweb.py -Rhello.php hello.noweb


###### Defining the command-line parser

```python
parser = argparse.ArgumentParser('NoWeb command line options.')
subparsers = parser.add_subparsers(help='Working modes')
parser.add_argument('input', metavar='FILE',
    help='input file to process, "-" for stdin')
parser.add_argument('-o', '--output', metavar='FILE', default='-',
    help='file to output to, "-" for stdout (default: %(default)s)')
parser.add_argument('-e', '--encoding', metavar='ENCODING',
    default='utf-8',
    help='Input and output encoding (default: %(default)s)')

# Create the parser for the "tangle" command
parser_tangle = subparsers.add_parser('tangle', help='tangle help')
parser_tangle.add_argument('-R', '--chunk', metavar='CHUNK',
    help='name of chunk to write to stdout')

# Create the parser for the "weave" command
parser_weave = subparsers.add_parser('weave', help='weave help')
parser_weave.add_argument('--default-code-syntax', metavar='LANGUAGE',
    help='use this syntax for code chunks')
parser_weave.add_argument('--add-links', action="store_true",
    help='Add HTML links to each code chunk')
parser_weave.set_defaults(chunk=None)
```


###### Parsing the command-line arguments

```python
<<Defining the command-line parser>>
args = parser.parse_args()
input = args.input
if args.input == '-':
    input = sys.stdin
```



# RECURSIVELY EXPANDING THE OUTPUT CHUNK

So far, so good. Now we need a recursive function to expand any chunks found
in the output chunk requested by the user. Take a deep breath.


###### Tangle chunks

```python
def tangle(self, chunkName, indent=""):
    if chunkName not in self.chunks:
        raise ValueError("No such chunk in document '%s'" % (chunkName,))

    for line in self.chunks[chunkName].lines:
        if line.type == Line.REFERENCE:
            assert(chunkName != None)
            if line.value not in self.chunks:
                err_pos = ''
                if self.last_fname:
                    err_pos = self.last_fname + ':'
                err_pos += '%u' % (line.position,)
                raise RuntimeError(
                    "%s: reference to non-existent chunk '%s'" % (err_pos, line.value))
            for line in self.tangle(line.value, indent + line.indentation):
                yield line
        else:
            yield self._indent_line(line, indent)
```

When weaving chunks need to be written using Markdown code-block syntax. This
either means indenting the block with 4 spaces. Alternatively when
GitHub-flavoured Markdown is chosen to get language-specific syntax-highlighting
we wrap the block in markers and mention the language to use for highlighting.


###### Weave chunks

```python
def weave(self, default_code_syntax=None, indent="", **kwargs):

    formatter = self.formatters.get(self.chunks[None].syntax)

    for line in self.chunks[None].lines:
        if line.type == Line.CHUNK_BEGIN:
            syntax = self.chunks[line.value].syntax or default_code_syntax
            for formatted_line in formatter(self, line, syntax, **kwargs):
                yield formatted_line

            code_lines = self.chunks[line.value].lines
            for formatted_line in formatter(self, code_lines, syntax, **kwargs):
                yield formatted_line

            line = line._replace(type=Line.CHUNK_END)
            for formatted_line in formatter(self, line, syntax, **kwargs):
                yield formatted_line
        else:
            line = self._indent_line(line, indent)
            for formatted_line in formatter(self, line, None, **kwargs):
                yield formatted_line
```


###### Format chunks

```python

def format_markdown(self, lines, code_syntax, add_links):
    if isinstance(lines, Line):
        lines = [lines]

    for line in lines:
        if line.type == Line.CHUNK_BEGIN:
            # Add a heading with the chunk's name.
            yield line._replace(value="\n")
            yield line._replace(value='###### ')
            yield line
            if add_links:
                name = "-".join(line.value.split()).lower()
                yield line._replace(value="".join([' <a name="', name, '"></a>']))
            yield line._replace(value="\n")
            yield line._replace(value="\n")

            if code_syntax:
                yield line._replace(value="```%s\n" % (code_syntax,))

        elif line.type == Line.CHUNK_END:
            yield line._replace(value='```\n' if code_syntax else "\n")

        elif line.type == Line.CODE:
            if not code_syntax:
                yield self._indent_line(line, "    ")
            else:
                yield line

        elif line.type == Line.REFERENCE:
            yield line._replace(value="".join(["<<", line.value, ">>", "\n"]))

        elif line.type == Line.DOCUMENTATION:
            assert(code_syntax == None)
            yield line

        else:
            raise TypeError("Unknown type of line")

formatters = {
    "markdown": format_markdown,
    "mdown":    format_markdown,
    "md":       format_markdown,

    "text":     format_markdown,
    "txt":      format_markdown,
    None:       format_markdown,
}

```



# OUTPUTTING THE CHUNKS

The last step is easy. We just call the recursive function and output the
result.


###### Outputting the chunks

```python
for line in lines:
    outfile.write(unicode(line).encode(self.encoding))
```

And we're done. We now have a tool to extract code from a literate programming
document. Try it on this blog post!



# DIRECTLY IMPORTING FROM PYTHON

In order to be able to import Noweb sources directly in Python a custom
ImportHook is provided. This hook conforms to PEP-302: the Importer Protocol.


###### ImportHook (PEP-302)

```python
class ImportHook(object):
    <<Hook registration methods>>

    def _get_module_info(self, fullname):
        prefix = fullname.replace('.', '/')
        # Is it a regular module?
        info = self._find_module_file(prefix, fullname)
        if info is not None:
            info['ispkg'] = False
            return info

        # Is it a package instead?
        prefix = os.path.join(prefix, "__init__")
        info = self._find_module_file(prefix, fullname)
        if info is not None:
            info['ispkg'] = True
            return info

        # Can't find the module
        raise ImportError(fullname)

    def _find_module_file(self, prefix, fullname):
        try:
            chunk = None
            if   fullname         in self.doc.chunks:
                chunk = fullname
            elif fullname + '.py' in self.doc.chunks:
                chunk = fullname + '.py'
            if chunk:
                bc_file = os.path.join(os.path.dirname(self.path), fullname + '.py')
                return dict(path=self.path, chunk=chunk)
        except AttributeError:
            pass

        path = prefix + '.py.nw'
        try:
            statinfo = os.stat(path)
            chunk = os.path.basename(os.path.realpath(path))[:-len('.nw')]
            if stat.S_ISREG(statinfo.st_mode):
                return dict(path=path, chunk=chunk)
        except OSError:
            pass

        return None

    <<Finding modules and their loaders>>
    <<Loading modules>>
    <<Importer Protocol Extensions>>
```

Part of the Importer Protocol entails finding out whether a given name can be
imported and if so giving Python a *loader* to import it with. We implement the
*finder* and *loader* entities using the same class and object.


###### Finding modules and their loaders

```python
def find_module(self, fullname, path=None):
    """Try to discover if we can find the given module."""
    try:
        self._get_module_info(fullname)
    except ImportError:
        return None
    else:
        return self
```

Loading of the object is done by deferring most work to other functions. All we
do directly is constructing a module if loading of it from the given chunk was
succesful.


###### Loading modules

```python
def load_module(self, fullname):
    """Load the specified module.

    This method locates the file and chunk for the specified module, loads and
    executes it and returns the created module object.
    """
    try:
        return sys.modules[fullname]
    except KeyError:
        pass

    info = self._get_module_info(fullname)
    code = self.get_code(fullname, info)
    if code is None:
        raise ImportError(fullname)
    module = imp.new_module(fullname)
    module.__file__ = info['chunk']
    module.__loader__ = self
    sys.modules[fullname] = module
    try:
        exec code in module.__dict__
        if self.path is None:
            module.__path__ = []
        else:
            module.__path__ = [self.path]
    except:
        sys.modules.pop(fullname, None)
        raise
    return module
```

In order to be able to use the ImportHook easily it has `install()` and
`uninstall()` methods that'll take care of hooking into Python's `meta_path` and
`path_hooks`. First they check to see whether ImportHook's already present and
then take appropriate action to add/remove itself to the list.

The `meta_path` hook causes files with a `.py.nw` extension to be imported
transparently *if* they have a named chunk with `$file.py` as name where $file
is the basename of the `.py.nw` file. Alternatively when sys.path contains a
filename ending in `.nw` chunks can be imported directly by specifying their
name.


###### Hook registration methods

```python
@classmethod
def install(cls):
    """Install this class into the import machinery."""
    for imp in sys.meta_path:
        try:
            if isinstance(imp, cls):
                break
        except TypeError:
            pass
    else:
        sys.meta_path.append(cls())
    for imp in sys.path_hooks:
        try:
            if issubclass(cls, imp):
                break
        except TypeError:
            pass
    else:
        sys.path_hooks.append(cls)
        sys.path_importer_cache.clear()

@classmethod
def uninstall(cls):
    """Uninstall this class from the import machinery."""
    to_rem = []
    for imp in sys.meta_path:
        try:
            if isinstance(imp, cls):
                to_rem.append(imp)
                break
        except TypeError:
            pass
    for imp in to_rem:
        sys.meta_path.remove(imp)
    to_rem = []
    for imp in sys.path_hooks:
        try:
            if issubclass(cls, imp):
                to_rem.append(imp)
        except TypeError:
            pass
    for imp in to_rem:
        sys.path_hooks.remove(imp)
    sys.path_importer_cache.clear()

def __init__(self, path=None):
    self.doc = None
    self.path = path
    if self.path is None:
        return

    try:
        if not self.path.endswith('.nw') or not stat.S_ISREG(os.stat(self.path).st_mode):
            raise ImportError(path)
        self.doc = Reader()
        self.doc.read(self.path)
    except (IOError, OSError):
        raise ImportError(path)
```

The Importer Protocol defines three optional extensions. One is to retrieve data
files, the second is to support module packaging tools and/or tools that analyze
module dependencies (for example Freeze), while the last is to support execution
of modules as scripts.

We implement all of these. Getting data files is implemented as getting named
chunks. Module introspection includes compiling of the code. Lastly getting the
filename (or `__file__`'s value) is implemented as getting the containing
chuck's name.


###### Importer Protocol Extensions

```python
def get_data(self, path):
    if self.doc is None or not path in self.doc.chunks:
        raise IOError(path)
    return self.doc.write(path)

def is_package(self, fullname, info=None):
    if info is None:
        info = self._get_module_info(fullname)
    return info['ispkg']

def get_code(self, fullname, info=None):
    if info is None:
        info = self._get_module_info(fullname)
    doc = self.doc
    if doc is None:
        with open(info['path'], 'U') as f:
            doc = Reader()
            doc.read(f)

    # Convert to string, while building a line-number conversion table
    outsrc = StringIO()
    line_map = {}
    for outlnum, line in enumerate(doc.tangle(info['chunk'])):
        inlnum = line.position
        outlnum += 1
        line_map[outlnum] = inlnum
        outsrc.write(line.value.encode(doc.encoding))

    # Parse output string to AST
    node = ast.parse(outsrc.getvalue(), info['path'], 'exec')
    # Rewrite line numbers on AST
    node = RewriteLine(line_map).visit(node)
    return compile(node, info['path'], 'exec')

def get_source(self, fullname, info=None):
    if info is None:
        info = self._get_module_info(fullname)
    with open(info['path'], 'U') as f:
        return f.read()

def get_filename(self, fullname, info=None):
    if info is None:
        info = self._get_module_info(fullname)
    return info['path']
```


###### AST Line-number re-writer

```python
class RewriteLine(ast.NodeTransformer):
    def __init__(self, line_map):
        self.line_map = line_map

    def visit(self, node):
        try:
            node = copy.copy(node)
            node.lineno = self.line_map[node.lineno]
        except (AttributeError,KeyError):
            pass
        return super(RewriteLine, self).visit(node)
```



# APPENDIX I: GENERATING THE SCRIPT

To generate noweb.py from this document, you first need a tool to extract the
code from it. You can use the original [noweb](http://www.cs.tufts.edu/~nr/noweb/)
tool, but that's a bit cumbersome to install, so it's easier to use the Python
script [noweb.py](http://github.com/JonathanAquino/noweb.py/raw/master/noweb.py).

Then you can generate noweb.py from noweb.py.nw as follows:

    noweb.py -Rnoweb.py noweb.py.nw -o noweb.py



# APPENDIX II: SUMMARY OF THE PROGRAM

Here's how the pieces we have discussed fit together:


###### noweb.py

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

<<License>>

"""
This program extracts code from a literate programming document in "noweb"
format.  It was generated from noweb.py.nw, itself a literate programming
document.
"""

from __future__ import unicode_literals

import argparse
import ast
import copy
import imp
import os
import re
import stat
import sys
import collections
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

<<AST Line-number re-writer>>
<<ImportHook (PEP-302)>>
<<Defining the processor>>

def main():
    <<Parsing the command-line arguments>>
    doc = Reader(encoding=args.encoding)
    doc.read(input)
    out = args.output
    if out == '-':
        out = sys.stdout

    # If args.chunk is None -> Weaver mode
    if args.chunk:
        lines = doc.tangle(args.chunk)
    else:
        lines = doc.weave(default_code_syntax=args.default_code_syntax,
            add_links=args.add_links)
    doc.write(lines, out)

if __name__ == "__main__":
    # Delete the pure-Python version of noweb to prevent cache retrieval
    sys.modules.pop('noweb', None)

    # Use noweb's loader to load itself
    try:
        noweb = ImportHook().load_module('noweb')
    except:
        import __main__ as noweb

    # Exceptions from within noweb should now be linked to the .nw source-file
    noweb.main()
```
