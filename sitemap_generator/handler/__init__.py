# =================================================================
#
# Authors: Benjamin Webb <bwebb@lincolninst.edu>
#
# Copyright (c) 2023 Benjamin Webb
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

'''Handler classs'''

import click
from pathlib import Path

from sitemap_generator.handler.filesystem import FileSystemHandler
from sitemap_generator.util import OPTION_VERBOSITY


@click.command()
@click.pass_context
@OPTION_VERBOSITY
@click.argument('filepath', type=click.Path())
@click.option('-s', '--uri_stem', type=str, default='https://geoconnex.us/',
              help='uri stem to be removed from short url for keyword')
def run(ctx, verbosity, filepath, uri_stem):
    filepath = Path(filepath)
    if filepath.is_dir():
        handler = FileSystemHandler(filepath, uri_stem)
        handler.handle()


if __name__ == '__main__':
    run()
