import os
import sys
import tokenize
import builtins
import importlib.util

from .pyvm2 import VirtualMachine

try:
    open_source = tokenize.open
except ImportError:
    def open_source(fname):
        return open(fname, "r", encoding='utf-8')

NoSource = Exception

def exec_code_object(code, env):
    vm = VirtualMachine()
    vm.run_code(code, f_globals=env)

def rsplit1(s, sep):
    parts = s.split(sep)
    return sep.join(parts[:-1]), parts[-1]

def run_python_module(modulename, args):
    glo, loc = globals(), locals()
    try:
        if '.' in modulename:
            packagename, name = rsplit1(modulename, '.')
            package = importlib.import_module(packagename)
        else:
            packagename, name = None, modulename
            package = None

        spec = importlib.util.find_spec(modulename)
        if spec is None:
            raise NoSource(f"module does not exist: {modulename}")

        filename = spec.origin
        if filename:
            args[0] = filename
            run_python_file(filename, args, package=packagename)

    except ImportError as e:
        raise NoSource(str(e))

def run_python_file(filename, args, package=None):
    old_main_mod = sys.modules['__main__']
    main_mod = importlib.new_module('__main__')
    sys.modules['__main__'] = main_mod
    main_mod.__file__ = filename
    if package:
        main_mod.__package__ = package
    main_mod.__builtins__ = builtins

    old_argv = sys.argv
    old_path0 = sys.path[0]
    sys.argv = args
    if package:
        sys.path[0] = ''
    else:
        sys.path[0] = os.path.abspath(os.path.dirname(filename))

    try:
        try:
            with open_source(filename) as source_file:
                source = source_file.read()
        except IOError:
            raise NoSource(f"No file to run: {filename}")

        if not source or source[-1] != '\n':
            source += '\n'
        code = compile(source, filename, "exec")
        exec_code_object(code, main_mod.__dict__)
    finally:
        sys.modules['__main__'] = old_main_mod
        sys.argv = old_argv
        sys.path[0] = old_path0
