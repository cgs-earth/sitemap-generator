# =================================================================
#
# Authors: Benjamin Webb <bwebb@lincolninst.edu>
#          Colton Loftus <cloftus@lincolninst.edu>
#
# Copyright (c) 2026 Lincoln Institute of Land Policy
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

import logging
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from sitemap_generator.util import (
    SitemapSourceWithMetadata,
    csv_to_sitemap_url_list,
    get_all_sitemap_sources,
    write_tree_to_file,
)


LOGGER = logging.getLogger(__name__)

URLSET = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</urlset>
"""

URLSET_FOREACH = """
<url>
    <loc>{}</loc>
    <lastmod>{}</lastmod>
</url>
"""

SITEMAPINDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</sitemapindex>
"""

BULK_SITEMAP_TEMPLATE = """<?xml version='1.0' encoding='utf-8'?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:ns1="http://geoconnex.us/schemas/sitemap">
    <url>
        <loc>{}</loc>
        <lastmod>2025-02-05T16:39:34Z</lastmod>
        <ns1:type>bulk</ns1:type>
    </url>
</urlset>"""


class FileSystemHandler:
    """Generate sitemaps from data in the filesystem and write them to disk"""

    def generate(
        self, namespace_input_dir: Path, uri_base: str, sitemap_output_dir: Path
    ) -> None:
        """
        Generate a sitemap index xml and sitemaps from the input directory
        and write them to disk in the output directory

        :returns: `None`
        """
        sources = get_all_sitemap_sources(namespace_input_dir)

        for source in sources:
            if source.metadata.get("skip_crawl"):
                LOGGER.info(f"Skipping generating sitemap for {source.path}")
                continue

            tree = self.make_sitemap(source)
            skip_including_in_sitemap_index = not tree
            if skip_including_in_sitemap_index:
                continue

            sitemap_location = source.canonical_sitemap_name(namespace_input_dir)
            output_path = (sitemap_output_dir / sitemap_location).with_suffix(".xml")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_tree_to_file(tree, output_path)
            LOGGER.info(f"Wrote {output_path} to disk")

        index = self.make_sitemap_index(
            base_uri=uri_base, sources=sources, root_dir=namespace_input_dir
        )
        write_tree_to_file(index, sitemap_output_dir / "sitemap.xml")
        LOGGER.info(f"Wrote sitemap index to disk at {sitemap_output_dir}/sitemap.xml")

    def make_sitemap(self, source: SitemapSourceWithMetadata) -> ET.ElementTree | Any:
        """
        Given a source within the filesystem tree, generate a sitemap XML
        associated with that source if it is appropriate to include,
        otherwise return None
        """
        match source.file_type:
            case "pregenerated_xml":
                with open(source.path) as f:
                    return ET.parse(f)
            case "regex_csv":
                return None
            case "one_to_one_csv":
                xml_root = ET.fromstring(URLSET)
                tree = ET.ElementTree(xml_root)

                for mapper in csv_to_sitemap_url_list(source.path):
                    url_element = ET.fromstring(
                        URLSET_FOREACH.format(mapper.geoconnex_pid, mapper.source_url)
                    )
                    xml_root.append(url_element)

                return tree
            case "bulk":
                xml_root = ET.fromstring(
                    BULK_SITEMAP_TEMPLATE.format(
                        source.metadata.get("bulk_container_image")
                    )
                )
                tree = ET.ElementTree(xml_root)
                return tree
            case _:
                raise ValueError(f"Unknown file type: {source.file_type}")

    def make_sitemap_index(
        self, base_uri: str, sources: list[SitemapSourceWithMetadata], root_dir: Path
    ) -> ET.ElementTree:
        """
        Builds a sitemap index XML from CSV files and their metadata.
        """

        xml_root = ET.fromstring(SITEMAPINDEX)
        tree = ET.ElementTree(xml_root)
        assert isinstance(tree, ET.ElementTree)

        for src in sources:
            # regex csvs shouldnt be a part of the sitemap,
            # only the pregenerated xml that is associated with them
            if src.file_type == "regex_csv":
                continue
            if src.metadata.get("skip_crawl"):
                continue
            sitemap_element = src.source_to_xml_for_index(base_uri, root_dir)
            ET.indent(sitemap_element, space="  ")
            xml_root.append(sitemap_element)

        return tree
