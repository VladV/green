import importlib
import logging
import os
import sys
import unittest


def getTests(target):
    loader = unittest.TestLoader()

    # DIRECTORY VARIATIONS - These will discover all tests in a directory
    # structure, whether or not they are accessible by the root package.

    # some/real/dir
    bare_dir = target
    # some.real.dir
    if ('.' in target) and (len(target) > 1):
        dot_dir  = target[0] + target[1:].replace('.', os.sep)
    else:
        dot_dir = None
    # pyzmq.tests  (Package (=dir) in PYTHONPATH, including installed ones)
    pkg_in_path_dir = None
    if target and (target[0] != '.'):
        try:
            filename = importlib.import_module(target).__file__
            if '__init__.py' in filename:
                pkg_in_path_dir = os.path.dirname(filename)
        except ImportError:
            pkg_in_path_dir = None

    # => DISCOVER DIRS
    for candidate in [bare_dir, dot_dir, pkg_in_path_dir]:
        if (candidate == None) or (not os.path.isdir(candidate)):
            continue
        # TestLoader.discover() rudely alters the path.  We'll have to restore
        # it ourselves.
        saved_sys_path = sys.path[:]
        tests = loader.discover(candidate)
        sys.path = saved_sys_path
        if tests and tests.countTestCases():
            logging.debug("Load method: DISCOVER - {}".format(candidate))
            return tests


    # DOTTED OBJECT - These will discover a specific object if it is
    # globally importable or importable from the current working directory.
    # Examples: pkg, pkg.module, pkg.module.class, pkg.module.class.func
    tests = None
    if target and (target[0] != '.'): # We don't handle relative dot objects
        if '' not in sys.path:
            sys.path.insert(0, '')
        try:
            tests = loader.loadTestsFromName(target)
        except ImportError:
            pass
        if tests and tests.countTestCases():
            logging.debug("Load method: DOTTED OBJECT - {}".format(target))
            return tests


    # FILE VARIATIONS - These will import a specific file and any tests
    # accessible from its scope.

    # some/file.py
    bare_file = target
    # some/file
    pyless_file = target + '.py'
    for candidate in [bare_file, pyless_file]:
        if (candidate == None) or (not os.path.isfile(candidate)):
            continue
        need_cleanup = False
        cwd = os.getcwd()
        if cwd.startswith('/private'):
            cwd = cwd[8:]
        if cwd != sys.path[0]:
            need_cleanup = True
            sys.path.insert(0, cwd)
        try:
            # In OS X, /var is a symlink to /private/var, and for some reason
            # this works better if we use the /var symlink
            slashed_path = target.replace('.py', '').replace(os.sep, '.')
            tests = loader.loadTestsFromName(slashed_path)
        except: # Any exception could occur here
            pass
        if need_cleanup:
            sys.path.remove(cwd)
        if tests and tests.countTestCases():
            logging.debug("Load method: FILE - {}".format(candidate))
            return tests


    # INSTALLED MODULE - (Unlike the installed package, we don't discover
    # inaccessible tests in this case -- we stick to tests accessible from the
    # module)
    if target and (target[0] != '.'): # We don't handle relative installed modules
        tests = None
        try:
            module = importlib.import_module(target)
            tests = loader.loadTestsFromModule(module)
        except ImportError:
            pass
        if tests and tests.countTestCases():
            return tests

    return None
