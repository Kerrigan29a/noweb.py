#!/usr/bin/env python
# -*- coding: utf8 -*-

from setuptools import setup, find_packages
from distutils.command.build import build
import tempfile
import bootstrap
import shutil
import os



class CustomBuild(build):
    def run(self):
        tmpdir = None
        try:
            # Create a temporary working directory
            tmpdir = tempfile.mkdtemp()

            # Create tmp script
            tmp_noweb = os.path.join(tmpdir, "noweb.py")

            # Tangle
            chunks = bootstrap.read("noweb.py.nw", "utf-8")
            lines = bootstrap.tangle("noweb.py", chunks, "")
            bootstrap.write(lines, "noweb.py", tmp_noweb, "utf-8")

            # And tangle again
            tangle_spell = "python " + tmp_noweb + " -o noweb.py tangle -R noweb.py noweb.py.nw"
            os.system(tangle_spell)

            # Weave
            os.system("python noweb.py -o README.md weave --default-code-syntax=python noweb.py.nw")

        finally:
            # Clean up our temporary working directory
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)
            build.run(self)



if __name__ == '__main__':
    setup(
        name='noweb.py',
        version='0.0.1',
        description="Literate programming tool",
        long_description=__doc__,
        author='Javier Escalada Gómez',
        author_email='kerrigan29a@gmail.com',
        url='http://github.com/Kerrigan29a/noweb.py',
        packages=find_packages(),
        include_package_data=True,
        install_requires=[
        ],
        scripts=[
            './noweb.py'
        ],
        license='BSD 3 Clause',
        cmdclass={
            "build": CustomBuild,
        }
        keywords="literate programming",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Topic :: Utilities",
            "Topic :: Software Development :: Code Generators",
            "Topic :: Software Development :: Documentation",
            "Topic :: Software Development :: Pre-processors",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
        ],
    )
