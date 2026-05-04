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

"""Handler classs"""

import click
from pathlib import Path

from sitemap_generator.handler.base import FileSystemHandler
from sitemap_generator.util import OPTION_VERBOSITY


@click.command()
@click.pass_context
@OPTION_VERBOSITY
@click.argument("namespace_input_dir", type=click.Path())
@click.option(
    "-u",
    "--uri_base",
    type=str,
    default="https://geoconnex.us",
    help="uri stem to be removed from short url for keyword",
)
@click.option(
    "-o",
    "--sitemap_output_dir",
    type=click.Path(),
    envvar='SITEMAP_DIR',
    default=Path("/tmp/sitemaps")
)
def run(
    ctx, verbosity, namespace_input_dir: Path, uri_base: str, sitemap_output_dir: Path
):
    namespace_dir = Path(namespace_input_dir)
    assert namespace_dir.is_dir(), f"{namespace_dir=} must be a directory"
    handler = FileSystemHandler()
    handler.generate(
        namespace_input_dir=Path(namespace_input_dir),
        uri_base=uri_base,
        sitemap_output_dir=Path(sitemap_output_dir),
    )


if __name__ == "__main__":
    run()
