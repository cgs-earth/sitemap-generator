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

from sitemap_generator.handler import Handler, SITEMAP_DIR
from sitemap_generator.util import walk_path, url_join

THIS_DIR = Path(__file__).parent.resolve()
NAMESPACE = THIS_DIR / 'data' / 'namespaces'

URI_STEM = 'https://geoconnex.us'
HANDLER = Handler(str(NAMESPACE), URI_STEM)


def test_handler():
    HANDLER.handle()
    glob = list(walk_path(SITEMAP_DIR, r'.*'))
    glob1 = list(walk_path(SITEMAP_DIR, r'.*xml'))
    assert len(glob) == len(glob1)


def test_sitemapindex():
    [sitemapindex] = list(walk_path(SITEMAP_DIR, r'.*_sitemap.xml'))
    assert sitemapindex.name == '_sitemap.xml'
    assert HANDLER._get_rel_path(sitemapindex) == '.'

    _ = HANDLER._get_filetime(sitemapindex)
    file_time = datetime.strptime(_, '%Y-%m-%dT%H:%M:%SZ')
    today = datetime.utcnow().strftime('%Y-%m-%d')
    assert file_time.strftime('%Y-%m-%d') == today

    tree = ET.parse(sitemapindex)
    root = tree.getroot()

    assert all(child.tag == 'sitemap' for child in root)
    assert all(URI_STEM in child.find('loc').text for child in root)

    hu08 = root.find('sitemap')
    loc = hu08.find('loc').text
    assert loc == 'https://geoconnex.us/sitemap/ref/hu08/hu08__0.xml'

    _ = hu08.find('lastmod').text
    lastmod = datetime.strptime(_, '%Y-%m-%dT%H:%M:%SZ')
    assert lastmod.strftime('%Y-%m-%d') != today


def test_urlset():
    [urlset] = list(walk_path(SITEMAP_DIR, r'.*links__0.xml'))
    assert urlset.name == 'links__0.xml'
    assert HANDLER._get_rel_path(urlset) == 'iow'

    _ = HANDLER._get_filetime(urlset)
    file_time = datetime.strptime(_, '%Y-%m-%dT%H:%M:%SZ')
    today = datetime.utcnow().strftime('%Y-%m-%d')
    assert file_time.strftime('%Y-%m-%d') != today

    namespace = url_join(URI_STEM, HANDLER._get_rel_path(urlset))
    assert namespace == 'https://geoconnex.us/iow'

    tree = ET.parse(urlset)
    root = tree.getroot()

    assert all(child.tag == 'url' for child in root)
    assert all(file_time.strftime('%Y-%m-%dT%H:%M:%SZ') ==
               child.find('lastmod').text for child in root)

    url = root.find('url')
    lastmod = url.find('lastmod').text
    assert lastmod == '2023-06-23T22:38:13Z'
