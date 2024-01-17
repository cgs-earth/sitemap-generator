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

from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from sitemap_generator.handler.base import SITEMAP_DIR
from sitemap_generator.handler.filesystem import FileSystemHandler
from sitemap_generator.util import walk_path, url_join

THIS_DIR = Path(__file__).parent.resolve()
NAMESPACE = THIS_DIR / 'data' / 'namespaces'

URI_STEM = 'https://geoconnex.us'
HANDLER = FileSystemHandler(str(NAMESPACE), URI_STEM)


def test_handler():
    HANDLER.handle()
    glob = list(walk_path(SITEMAP_DIR, r'.*'))
    glob1 = list(walk_path(SITEMAP_DIR, r'.*xml'))
    assert len(glob) == len(glob1)


def test_sitemapindex():
    [sitemapindex] = list(walk_path(SITEMAP_DIR, r'.*_sitemap.xml'))
    assert sitemapindex.name == '_sitemap.xml'
    assert HANDLER.get_rel_path(sitemapindex) == '.'

    _ = HANDLER.get_filetime(sitemapindex)
    file_time = datetime.strptime(_, '%Y-%m-%dT%H:%M:%SZ')
    today = datetime.utcnow().strftime('%Y-%m-%d')
    assert file_time.strftime('%Y-%m-%d') == today

    tree = ET.parse(sitemapindex)
    root = tree.getroot()

    assert all('sitemap' in child.tag for child in root)
    for child in root:
        assert URI_STEM in ''.join(child.itertext())
    assert all(URI_STEM in ''.join(child.itertext()) for child in root)


def test_urlset():
    [urlset] = list(walk_path(SITEMAP_DIR, r'.*links__0.xml'))
    assert urlset.name == 'links__0.xml'
    assert HANDLER.get_rel_path(urlset) == 'iow'

    _ = HANDLER.get_filetime(urlset)
    file_time = datetime.strptime(_, '%Y-%m-%dT%H:%M:%SZ')
    today = datetime.utcnow()
    assert file_time != today

    namespace = url_join(URI_STEM, HANDLER.get_rel_path(urlset))
    assert namespace == 'https://geoconnex.us/iow'
