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

import click
import csv
import logging
from pathlib import Path
import re
import sys
from typing import Iterator
import xml.etree.ElementTree as ET

LOGGER = logging.getLogger(__name__)

SITEMAP_ARGS = {'encoding': 'utf-8', 'xml_declaration': True}
SITEMAPINDEX = '''<?xml version="1.0"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</sitemapindex>
'''
SITEMAPINDEX_FOREACH = '''
<sitemap>
    <loc>{}</loc>
    <lastmod>{}</lastmod>
</sitemap>
'''
URLSET = '''<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</urlset>
'''
URLSET_FOREACH = '''
<url>
    <loc>{}</loc>
    <lastmod>{}</lastmod>
</url>
'''


def write_tree(tree, file):
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    tree.write(file, **SITEMAP_ARGS)
    try:
        ET._namespace_map.pop('http://www.sitemaps.org/schemas/sitemap/0.9')
    except KeyError:
        print('No default namespace')


def get_smi():
    root = ET.fromstring(SITEMAPINDEX)
    tree = ET.ElementTree(root)
    try:
        ET.indent(tree)
    except AttributeError:
        LOGGER.warning('Unable to indent')
    return tree, root


def add_smi_node(node, loc, lastmod):
    _ = SITEMAPINDEX_FOREACH.format(loc, lastmod)
    node.append(ET.fromstring(_))


def get_urlset():
    root = ET.fromstring(URLSET)
    tree = ET.ElementTree(root)
    try:
        ET.indent(tree)
    except AttributeError:
        LOGGER.warning('Unable to indent')
    return tree, root


def add_urlset_node(node, loc, lastmod):
    _ = URLSET_FOREACH.format(loc, lastmod)
    node.append(ET.fromstring(_))


def walk_path(path: Path, regex: str) -> Iterator[Path]:
    """
    Walks os directory path collecting all files.

    :param path: required, string. os directory.

    :returns: list. Iterator of file paths.
    """
    path = Path(path)
    reg = re.compile(regex)
    if path.is_dir():
        pattern = '**/*'
        for f in path.glob(pattern):
            if f.is_file() and reg.match(f.name):
                yield Path(f)
    else:
        yield Path(path)


def url_join(*parts):
    """
    helper function to join a URL from a number of parts/fragments.
    Implemented because urllib.parse.urljoin strips subpaths from
    host urls if they are specified
    Per https://github.com/geopython/pygeoapi/issues/695

    :param parts: list of parts to join

    :returns: str of resulting URL
    """
    return '/'.join([str(p).strip().strip('/') for p in parts])


def parse(filename: Path, n: int = 50000) -> list:
    """
    Parses file to a CSV

    :param filename: `Path` of source file to parse
    :param n: `int` size of each chunk

    :returns: `list`
    """
    with filename.open('r') as fh:
        csv_reader = csv.reader(fh)
        headers = [h.strip() for h in next(csv_reader)]  # noqa
        lines = [line for line in csv_reader]
        return chunkify(lines, n)


def chunkify(input: list, n: int) -> list:
    """
    Breaks a list of strings into chunks.

    :param input: `list` to be chunkified
    :param n: `int` size of each chunk

    :return: `list` with each sublist length up to the size of n.
    """
    return [(input[i:i + n]) for i in range(0, len(input), n)]


def OPTION_VERBOSITY(f):
    logging_options = ['ERROR', 'WARNING', 'INFO', 'DEBUG']
    log_format = \
        '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    date_format = '%Y-%m-%dT%H:%M:%SZ'

    def callback(ctx, param, value):

        if value is not None:
            logging.basicConfig(level=value, datefmt=date_format,
                                format=log_format, stream=sys.stdout)
        return True

    return click.option('--verbosity', '-v',
                        type=click.Choice(logging_options),
                        help='Verbosity',
                        default='DEBUG',
                        callback=callback)(f)
