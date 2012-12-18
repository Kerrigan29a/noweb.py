#!/usr/bin/env python

#
# noweb.py
# By Jonathan Aquino (jonathan.aquino@gmail.com)
#
# This program extracts code from a literate programming document in "noweb" format.
# It was generated from noweb.py.txt, itself a literate programming document.
# For more information, including the original source code and documentation,
# see http://jonaquino.blogspot.com/2010/04/nowebpy-or-worlds-first-executable-blog.html
#

import argparse
import re
cmd_line_parser = argparse.ArgumentParser('NoWeb command line options.')
cmd_line_parser.add_argument('infile',                            metavar='FILE',  type=argparse.FileType('r'),              help='input file to process, "-" for stdin')
cmd_line_parser.add_argument('-o', '--output', dest='outfile',    metavar='FILE',  type=argparse.FileType('w'), default='-', help='file to output to, "-" for stdout')

#FIXME: Apparently Python doesn't want groups within groups?
#_output_mode_dependent = cmd_line_parser.add_mutually_exclusive_group(required=True)
_output_mode_dependent = cmd_line_parser

_tangle_options = _output_mode_dependent.add_argument_group('tangle', 'Tangle options')
_tangle_options.add_argument('-R', '--chunk', metavar='CHUNK',    help='name of chunk to write to stdout')

_weave_options  = _output_mode_dependent.add_argument_group('weave',  'Weave options')
_weave_options.add_argument('-w', '--weave', action='store_true', help='weave output instead of tangling')
_weave_options.add_argument('--github-syntax', metavar='LANGUAGE', help='use GitHub-Flavoured MarkDown as output for chunks')
chunk_re         = re.compile(r'<<(?P<name>[^>]+)>>')
chunk_def        = re.compile(chunk_re.pattern + r'=')
chunk_at         = re.compile(r'^@@(?=\s|$)')
chunk_end        = re.compile(r'^@(?=\s|$)')
chunk_invocation = re.compile(r'^(?P<indent>\s*)' + chunk_re.pattern + r'\s*$')

def expand(chunkName, indent=""):
    for line in chunks[chunkName]:
        match = chunk_invocation.match(line)
        if match:
            for line in expand(match.group('name'), indent + match.group('indent')):
                yield line
        else:
            match = chunk_def.match(line)
            if match and args.weave:
                if args.github_syntax:
                    yield '\n###### %s\n```%s\n' % (match.group('name'), args.github_syntax,)
                else:
                    yield '\n    <<%s>>=\n' % (match.group('name'),)
                for def_line in chunks[match.group('name')]:
                    if not args.github_syntax:
                        yield '    '
                    yield def_line
                if args.github_syntax:
                    yield '```\n'
                else:
                    yield '    @\n'
            elif line and line != '\n':
                yield indent + line
            else:
                yield line

if __name__ == "__main__":
    args = cmd_line_parser.parse_args()
    chunkName = None
    chunks = {chunkName: []}

    for line in args.infile:
        match = chunk_def.match(line)
        if match and not chunkName:
            chunks[chunkName].append(line)
            chunkName = match.group('name')
            chunks[chunkName] = []
        else:
            if chunk_end.match(line):
                chunkName = None
            else:
                line = chunk_at.sub('@', line)
                chunks[chunkName].append(line)
    for line in expand(args.chunk):
        args.outfile.write(line)
