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
import sys
parser = argparse.ArgumentParser('NoWeb command line options.')
parser.add_argument('-R', '--chunk', metavar='CHUNK', required=True, dest='chunk_name', help='name of chunk to write to stdout')
parser.add_argument('infile', metavar='FILE', type=argparse.FileType('r'), help='input file to process, "-" for stdin')

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
    expandedChunkLines = []
    for line in chunkLines:
        match = re.match("(\s*)" + OPEN + "([^>]+)" + CLOSE + "\s*$", line)
        if match:
            expandedChunkLines.extend(expand(match.group(2), indent + match.group(1)))
        else:
            expandedChunkLines.append(indent + line)
    return expandedChunkLines

for line in expand(args.chunk_name, ""):
    print line,
