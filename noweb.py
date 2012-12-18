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
parser = argparse.ArgumentParser('NoWeb command line options.')
parser.add_argument('-R', '--chunk',  dest='chunk_name', metavar='CHUNK', required=True,                            help='name of chunk to write to stdout')
parser.add_argument('infile',                            metavar='FILE',  type=argparse.FileType('r'),              help='input file to process, "-" for stdin')
parser.add_argument('-o', '--output', dest='outfile',    metavar='FILE',  type=argparse.FileType('w'), default='-', help='file to output to, "-" for stdout')

args = parser.parse_args()
chunkName = None
chunks = {}
OPEN = "<<"
CLOSE = ">>"
for line in args.infile:
    match = re.match(OPEN + "([^>]+)" + CLOSE + "=", line)
    if match:
        chunkName = match.group(1)
        chunks[chunkName] = []
    else:
        match = re.match("@", line)
        if match:
            chunkName = None
        elif chunkName:
            chunks[chunkName].append(line)

def expand(chunkName, indent):
    chunkLines = chunks[chunkName]
    for line in chunkLines:
        match = re.match("(\s*)" + OPEN + "([^>]+)" + CLOSE + "\s*$", line)
        if match:
            for line in expand(match.group(2), indent + match.group(1)):
                yield line
        else:
            yield indent + line

for line in expand(args.chunk_name, ""):
    args.outfile.write(line)
