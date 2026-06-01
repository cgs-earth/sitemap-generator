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
from xml.etree import ElementTree

from sitemap_generator.handler.base import FileSystemHandler
from pytest import fixture

from sitemap_generator.util import get_all_sitemap_sources, write_tree_to_file
import tempfile


@fixture()
def handler():
    return FileSystemHandler()


def test_sitemap_index_generation(handler: FileSystemHandler):
    sources = get_all_sitemap_sources(Path(__file__).parent / "data" / "namespaces")
    for source in sources:
        assert source.metadata, (
            f"Sitemap source for file {source.path.name} has no metadata"
        )
    tree: ElementTree.ElementTree = handler.make_sitemap_index(
        "https://geoconnex.us", sources, Path(__file__).parent / "data"
    )

    sources_to_crawl = len(
        [src for src in sources if not src.metadata.get("skip_crawling")]
    )
    sitemaps_in_index = len(tree.findall("{*}sitemap"))
    assert sources_to_crawl == sitemaps_in_index, (
        f"There should be one sitemap per source but got {sitemaps_in_index=} and {sources_to_crawl=}"
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
            assert elem.find("{*}sitemap_id") is not None, (
                f"Missing sitemap_id in {elem.tag}"
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


def test_sitemap_index_generation_with_missing_metadata(handler: FileSystemHandler):
    sources = get_all_sitemap_sources(
        Path(__file__).parent / "data" / "namespaces_with_missing_metadata"
    )
    tree: ElementTree.ElementTree = handler.make_sitemap_index(
        "https://geoconnex.us", sources, Path(__file__).parent / "data"
    )

    for elem in tree.iter():
        if elem.tag is ElementTree.Comment or elem.tag is ElementTree.PI:
            continue

        # skip root element (sitemapindex)
        if elem.tag.endswith("sitemapindex"):
            continue

        if elem.tag.endswith("sitemap"):
            loc = elem.find("{*}loc")
            lastmod = elem.find("{*}lastmod")

            assert loc is not None, f"Missing loc in sitemap {elem.tag}"
            assert lastmod is not None, f"Missing lastModified in sitemap {elem.tag}"

            # test_hu08 should have a contact_email
            locText = loc.text
            assert locText, f"Missing loc text in sitemap with loc {loc.text}"
            if loc is not None and "hu08" in locText:
                assert elem.find("{*}contact_email") is not None, (
                    f"Missing contact_email in sitemap with loc {loc.text}"
                )
            else:
                assert elem.find("{*}contact_email") is None, (
                    f"Unexpected contact_email in sitemap with loc {loc.text}"
                )

    tmpFile = tempfile.NamedTemporaryFile()
    write_tree_to_file(tree, Path(tmpFile.name))
    assert Path(tmpFile.name).exists()


def test_sitemap_bulk_handler(handler: FileSystemHandler):
    sources = get_all_sitemap_sources(Path(__file__).parent / "data" / "namespaces")

    bulk_source = [src for src in sources if src.file_type == "bulk"][0]
    bulk_sitemap = handler.make_sitemap(bulk_source)

    def assert_elements_equal(e1: ElementTree.Element, e2: ElementTree.Element):
        # Don't check lastmod since it includes a timestamp; assume it is fine
        if e1.tag.endswith("lastmod"):
            return
        assert e1.tag == e2.tag
        assert (e1.text or "").strip() == (e2.text or "").strip(), (
            f"Different text {e1.text} and {e2.text} for tag {e1.tag}"
        )
        assert e1.attrib == e2.attrib, (
            f"Different attributes {e1.attrib} and {e2.attrib} for tag {e1.tag}"
        )

        assert len(e1) == len(e2), f"Different number of children: {e1.tag}"

        for c1, c2 in zip(e1, e2):
            assert_elements_equal(c1, c2)

    expected = ElementTree.fromstring(
        """<?xml version='1.0' encoding='utf-8'?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:ns1="http://geoconnex.us/schemas/sitemap">
            <url>
                <loc>internetofwater/gnis_bulk_rdf:latest</loc>
            </url>
        </urlset>
        """
    )
    root = bulk_sitemap.getroot()
    assert root is not None
    # compare root elements
    assert_elements_equal(root, expected)
