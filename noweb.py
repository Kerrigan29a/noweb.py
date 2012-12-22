#!/usr/bin/env python

# Copyright (c) 2010  Jonathan Aquino (jonathan.aquino@gmail.com)
# Copyright (c) 2012  Giel van Schijndel (me@mortis.eu)

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
class NowebReader(object):
    chunk_re         = re.compile(r'<<(?P<name>[^>]+)>>')
    chunk_def        = re.compile(chunk_re.pattern + r'=')
    chunk_at         = re.compile(r'^@@(?=\s|$)')
    chunk_end        = re.compile(r'^@(?:\s(?P<text>.*))?$', re.DOTALL)
    chunk_invocation = re.compile(r'^(?P<indent>\s*)' + chunk_re.pattern + r'\s*$')

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
        finally:
            if isinstance(file, basestring):
                infile.close()

    def expand(self, chunkName, indent="", weave=False, github_syntax=None):
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
                else:
                    # Only add indentation to non-empty lines
                    if line and line != '\n':
                        line = indent + line
                    yield lnum, line

    def write(self, chunkName, file=None, weave=False, github_syntax=None):
        if isinstance(file, basestring) or file is None:
            outfile = StringIO()
        else:
            outfile = file

        for _, line in self.expand(chunkName, weave=weave, github_syntax=github_syntax):
            outfile.write(line)

        if file is None:
            return outfile.getvalue()
        elif isinstance(file, basestring):
            with open(file, 'w') as f:
                f.write(outfile.getvalue())

if __name__ == "__main__":
    args = cmd_line_parser.parse_args()

    if args.infile == '-':
        infile = sys.stdin
    else:
        infile = open(args.infile, 'r')
    doc = NowebReader()
    doc.read(infile)
    out = args.output
    if out == '-':
        out = sys.stdout
    doc.write(args.chunk, out, weave=args.weave, github_syntax=args.github_syntax)
