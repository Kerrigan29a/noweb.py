#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2010  Jonathan Aquino (jonathan.aquino@gmail.com)
# Copyright (c) 2014  Javier Escalada Gómez (kerrigan29a@gmail.com)



import re
import codecs



OPEN = "<<"
CLOSE = ">>"
CHUNK = "(?:.*:)?([^>]+)"



def read(infile, encoding):
    assert(infile)
    assert(encoding)

    chunks = {}
    chunkName = None
    with codecs.open(infile, "r", encoding=encoding) as f:
        for line in f:
            match = re.match(OPEN + CHUNK + CLOSE + "=", line)
            if match:
                chunkName = match.group(1)
                chunks[chunkName] = []
            else:
                match = re.match("@", line)
                if match:
                    chunkName = None
                elif chunkName:
                    chunks[chunkName].append(line)
    return chunks



def tangle(chunkName, chunks, indent):
    assert(chunkName)
    assert(chunks)
    assert(indent != None)

    chunkLines = chunks[chunkName]
    expandedChunkLines = []
    for line in chunkLines:
        match = re.match("(\s*)" + OPEN + CHUNK + CLOSE + "\s*$", line)
        if match:
            expandedChunkLines.extend(tangle(match.group(2), chunks, indent + match.group(1)))
        else:
            expandedChunkLines.append(indent + line)
    return expandedChunkLines



def write(lines, chunkName, output, encoding):
    assert(lines)
    assert(chunkName)
    assert(output)

    with codecs.open(output, "w", encoding=encoding) as f:
        for line in lines:
            f.write(line)


def main():
    import argparse

    cmd_line_parser = argparse.ArgumentParser('Bootstrap NoWeb command line options.')
    cmd_line_parser.add_argument('infile',         metavar='FILE',
        help='input file to process, "-" for stdin')
    cmd_line_parser.add_argument('-o', '--output', metavar='FILE', default='-',
        help='file to output to, "-" for stdout (default: %(default)s)')
    cmd_line_parser.add_argument('-e', '--encoding', metavar='ENCODING', default='utf-8',
        help='Input and output encoding (default: %(default)s)')
    cmd_line_parser.add_argument('-R', '--chunk', metavar='CHUNK',
        help='name of chunk to write to stdout')
    args = cmd_line_parser.parse_args()

    chunks = read(args.infile, args.encoding)
    lines = tangle(args.chunk, chunks, "")
    write(lines, args.chunk, args.output, args.encoding)


if __name__ == "__main__":
    exit(main())
