#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2010  Jonathan Aquino (jonathan.aquino@gmail.com)
# Copyright (c) 2012  Giel van Schijndel (me@mortis.eu)
# Copyright (c) 2014  Javier Escalada Gómez (kerrigan29a@gmail.com)

"""
This program extracts code from a literate programming document in "noweb"
format.  It was generated from noweb.py.nw, itself a literate programming
document.
"""

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
class ImportHook(object):
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

        def find_module(self, fullname, path=None):
            """Try to discover if we can find the given module."""
            try:
                self._get_module_info(fullname)
            except ImportError:
                return None
            else:
                return self
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
        for outlnum, (inlnum, line) in enumerate(doc.expand(info['chunk'])):
            outlnum += 1
            line_map[outlnum] = inlnum
            outsrc.write(line.encode(doc.encoding))

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
Chunk = collections.namedtuple("Chunk",
    ["syntax", "lines", "position"])



class Line(collections.namedtuple("Line",
    ["type", "value", "indentation", "position"])):
    __slots__ = ()
    NORMAL = 0
    REFERENCE = 1
    DECLARATION = 2


class Reader(object):
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
                        # TODO: Do something with options.syntax
                        continue
                match = self.chunk_def.match(line)
                if match and not chunkName:
                    chunkName = match.group('name')
                    chunkSyntax = match.group('syntax')
                    # Append reference to code in documentation
                    self.chunks[None].lines.append(Line(type=Line.DECLARATION,
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
                            try:
                                self.chunks[chunkName].lines[-1][-1].append((lnum + 1, text))
                            except (IndexError, AttributeError):
                                pass
                    else:
                        line = self.chunk_at.sub('@', line)
                        match = self.chunk_invocation.match(line)
                        if match:
                            sub_chunk = match.group('name')
                            sub_indent = match.group('indent')
                            self.chunks[chunkName].lines.append(Line(type=Line.REFERENCE,
                                value=sub_chunk, indentation=sub_indent, position=lnum + 1))
                        else:
                            self.chunks[chunkName].lines.append(Line(type=Line.NORMAL,
                                value=line, indentation="", position=lnum + 1))
        finally:
            if isinstance(file, basestring):
                input.close()

    def expand(self, chunkName, indent="", weave=False, default_code_syntax=None):
        print("[DEBUG] chunkName = " + (chunkName if chunkName else "None"))
        print "[DEBUG] weave = " + str(weave)
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
                for lnum, line in self.expand(line.value, indent + line.indentation, weave):
                    yield lnum, line

            elif line.type == Line.DECLARATION:
                assert(weave)
                assert(chunkName == None)
                print u"[DEBUG] line (weave) = " + unicode(line)

                # Add a heading with the chunk's name.
                yield line.position, '\n'
                yield line.position, '###### %s\n' % line.value
                yield line.position, '\n'

                syntax = self.chunks[line.value].syntax or default_code_syntax
                if syntax:
                    yield line.position, '```%s\n' % (syntax,)

                for line in self.chunks[line.value].lines:
                    result_line = line.value
                    if not syntax:
                        result_line = '    ' + result_line
                    yield line.position, result_line

                if syntax:
                    yield line.position, '```\n'

                yield line.position, '\n'

            else:
                # Only add indentation to non-empty lines
                if line.value and line.value not in ('\n', '\r\n'):
                    result_line = indent + line.value
                else:
                    result_line = line.value
                yield line.position, result_line

    def write(self, chunkName, file=None, weave=False, default_code_syntax=None):
        if isinstance(file, basestring) or file is None:
            outfile = StringIO()
        else:
            outfile = file

        if chunkName not in self.chunks:
            raise RuntimeError("No such chunk in document '%s'" % (chunkName,))
        for _, line in self.expand(chunkName, weave=weave, default_code_syntax=default_code_syntax):
            outfile.write(line.encode(self.encoding))

        if file is None:
            return outfile.getvalue()
        elif isinstance(file, basestring):
            with open(file, 'w') as f:
                txt = outfile.getvalue()
                if isinstance(txt, unicode):
                    txt = txt.encode(self.encoding)
                f.write(txt)

def main():

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

    # XXX: This is just a dirty fix to change in the future
    parser_tangle.set_defaults(weave_mode=False)

    # Create the parser for the "weave" command
    parser_weave = subparsers.add_parser('weave', help='weave help')
    parser_weave.add_argument('--default-code-syntax', metavar='LANGUAGE',
        help='use this syntax for code chunks')

    # XXX: This is just a dirty fix to change in the future
    parser_weave.set_defaults(weave_mode=True)

    args = parser.parse_args()

    input = args.input
    if args.input == '-':
        input = sys.stdin
    doc = Reader(encoding=args.encoding)
    print "[DEBUG] READING"
    doc.read(input)
    out = args.output
    if out == '-':
        out = sys.stdout

    if args.weave_mode:
        print "[DEBUG] WRITING (WEAVE)"
    else:
        print "[DEBUG] WRITING (TANGLE)"

    doc.write(
        None if args.weave_mode else args.chunk,
        out,
        weave=args.weave_mode,
        default_code_syntax=args.default_code_syntax if args.weave_mode else None)

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
