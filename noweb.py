#!/usr/bin/env python

# Copyright (c) 2010  Jonathan Aquino (jonathan.aquino@gmail.com)
# Copyright (c) 2012  Giel van Schijndel (me@mortis.eu)

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
            self.doc = NowebReader()
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
                doc = NowebReader()
                doc.read(f)

        # Convert to string, while building a line-number conversion table
        outsrc = StringIO()
        line_map = {}
        for outlnum, (inlnum, line) in enumerate(doc.expand(info['chunk'])):
            outlnum += 1
            line_map[outlnum] = inlnum
            outsrc.write(line)

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
class NowebReader(object):
    chunk_re         = re.compile(r'<<(?P<name>[^>]+)>>')
    chunk_def        = re.compile(chunk_re.pattern + r'=')
    chunk_at         = re.compile(r'^@@(?=\s|$)')
    chunk_end        = re.compile(r'^@(?:\s(?P<text>.*))?$', re.DOTALL)
    chunk_invocation = re.compile(r'^(?P<indent>\s*)' + chunk_re.pattern + r'\s*$')

    def __init__(self, file=None):
        self.chunks = {None: []}
        self.last_fname = None

        if file is not None:
            self.read(file)

    def read(self, file):
        if isinstance(file, basestring):
            infile = open(file)
            self.last_fname = file
        else:
            infile = file
            self.last_fname = None
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
                sub_chunk = match.group('name')
                sub_indent = indent + match.group('indent')
                if sub_chunk not in self.chunks:
                    err_pos = ''
                    if self.last_fname:
                        err_pos = self.last_fname + ':'
                    err_pos += '%u' % (lnum,)
                    raise RuntimeError("%s: reference to non-existent chunk '%s'" % (err_pos, sub_chunk))
                for lnum, line in self.expand(sub_chunk, sub_indent, weave):
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

def main():
    args = cmd_line_parser.parse_args()

    infile = args.infile
    if args.infile == '-':
        infile = sys.stdin
    doc = NowebReader()
    doc.read(infile)
    out = args.output
    if out == '-':
        out = sys.stdout
    doc.write(args.chunk, out, weave=args.weave, github_syntax=args.github_syntax)

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
