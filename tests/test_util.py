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

from pathlib import Path

from sitemap_generator import util

THIS_DIR = Path(__file__).parent.resolve()
NAMESPACE = THIS_DIR / 'data' / 'namespaces'


def test_walk_path():
    glob_all = list(util.walk_path(NAMESPACE, r'.*'))
    assert len(glob_all) >= 2

    glob = util.walk_path(NAMESPACE, r'.*csv')
    assert len(list(glob)) < len(glob_all)

    glob = util.walk_path(NAMESPACE, r'.*xml')
    assert len(list(glob)) < len(glob_all)


def test_parse_and_chunk():
    glob = util.walk_path(NAMESPACE / 'ref', r'.*csv')
    hu08 = next(glob)
    assert hu08.stem == 'hu08'

    lines = util.parse(hu08)
    assert len(lines) == 1
    assert len(lines[-1]) == 2399

    chunks = util.parse(hu08, 1000)
    assert len(chunks) == 3
    assert len(chunks[0]) == 1000
    assert len(chunks[-1]) == 399

    [lines] = util.parse(hu08)
    chunks = util.chunkify(lines, 100)
    assert len(chunks) == 24
    assert len(chunks[0]) == 100
    assert len(chunks[-1]) == 99
