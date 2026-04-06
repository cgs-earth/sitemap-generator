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

import datetime
from pathlib import Path
from xml.etree import ElementTree

from sitemap_generator.handler.base import FileSystemHandler
from pytest import fixture

from sitemap_generator.util import get_all_sitemap_sources, write_tree_to_file
import tempfile


@fixture()
def handler():
    return FileSystemHandler()


def test_sitemap_index_generation(handler):
    sources = get_all_sitemap_sources(Path(__file__).parent / "data")
    for source in sources:
        assert source.metadata
    tree: ElementTree.ElementTree = handler.make_sitemap_index(
        "https://geoconnex.us", sources, Path(__file__).parent / "data"
    )

    for elem in tree.iter():
        if elem.tag is ElementTree.Comment or elem.tag is ElementTree.PI:
            continue

        # skip root element (sitemapindex)
        if elem.tag.endswith("sitemapindex"):
            continue

        # only validate sitemap entries
        if elem.tag.endswith("sitemap"):
            assert elem.find("{*}loc") is not None, f"Missing loc in {elem.tag}"
            assert elem.find("{*}lastmod") is not None, (
                f"Missing lastModified in {elem.tag}"
            )
            assert elem.find("{*}contact_email") is not None, (
                f"Missing contact_email in {elem.tag}"
            )
    tmpFile = tempfile.NamedTemporaryFile()
    write_tree_to_file(tree, Path(tmpFile.name))
    assert Path(tmpFile.name).exists()

    written_data = Path(tmpFile.name).read_text()
    assert "hu08" in written_data
    assert "contact_email" in written_data
