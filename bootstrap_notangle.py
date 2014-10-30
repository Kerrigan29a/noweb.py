#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2010  Jonathan Aquino (jonathan.aquino@gmail.com)
# Copyright (c) 2014  Javier Escalada Gómez (kerrigan29a@gmail.com)



import sys
import re
import argparse
import codecs



cmd_line_parser = argparse.ArgumentParser('Bootstrap NoWeb command line options.')
cmd_line_parser.add_argument('infile',         metavar='FILE',              help='input file to process, "-" for stdin (default: %(default)s)')
cmd_line_parser.add_argument('-o', '--output', metavar='FILE', default='-', help='file to output to, "-" for stdout (default: %(default)s)')
cmd_line_parser.add_argument('-e', '--encoding', metavar='ENCODING', default='utf-8', help='Input and output encoding (default: %(default)s)')

_tangle_options = cmd_line_parser.add_argument_group('tangle', 'Tangle options')
_tangle_options.add_argument('-R', '--chunk', metavar='CHUNK',    help='name of chunk to write to stdout')
args = cmd_line_parser.parse_args()



outputChunkName = args.chunk
chunkName = None
chunks = {}
OPEN = "<<"
CLOSE = ">>"

with codecs.open(args.infile, "r", encoding=args.encoding) as f:
    for line in f:
        match = re.match(OPEN + "(?:.*:)?([^>]+)" + CLOSE + "=", line)
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
        match = re.match("(\s*)" + OPEN + "(?:.*:)?([^>]+)" + CLOSE + "\s*$", line)
        if match:
            expandedChunkLines.extend(expand(match.group(2), indent + match.group(1)))
        else:
            expandedChunkLines.append(indent + line)
    return expandedChunkLines

with codecs.open(args.output, "w", encoding=args.encoding) as f:
    for line in expand(outputChunkName, ""):
        f.write(line)
