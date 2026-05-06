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

from dataclasses import dataclass
import datetime
from typing import Generator, Literal, NamedTuple, Any

import click
import csv
import logging
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import json


LOGGER = logging.getLogger(__name__)


class UrlToGeoconnexPid(NamedTuple):
    source_url: str
    geoconnex_pid: str


def csv_to_sitemap_url_list(csv_path: Path) -> Generator[UrlToGeoconnexPid, None, None]:
    with csv_path.open() as f:
        reader = csv.reader(f)

        header = next(reader)  # read first row (column names)
        id_index = header.index("id")  # get position of 'id' column
        target_index = header.index("target")  # get position of 'target' column

        for row in reader:
            yield UrlToGeoconnexPid(
                geoconnex_pid=row[id_index], source_url=row[target_index]
            )


def write_tree_to_file(tree: ET.ElementTree | Any, file: Path):
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.register_namespace("geoconnex", "https://geoconnex.us")
    tree.write(file_or_filename=file, encoding="utf-8", xml_declaration=True)


def is_regex_csv(path: Path) -> bool:
    with open(path) as f:
        reader = csv.reader(f)
        _ = next(reader)
        rows = 0
        for _ in reader:
            rows += 1
            if rows > 5:
                break
        return rows < 5


def datettime_to_sitemap_iso_format(timestamp: datetime.datetime) -> str:
    return (
        timestamp.astimezone(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass
class SitemapSourceWithMetadata:
    path: Path
    file_type: Literal["regex_csv", "one_to_one_csv", "pregenerated_xml", "bulk"]
    last_modified: datetime.datetime
    metadata: dict

    def canonical_sitemap_name(self, root_relative_dir: Path) -> str:
        cleaned_path = (
            self.path.relative_to(root_relative_dir).with_suffix("")  # remove suffix
        )

        if cleaned_path.name == cleaned_path.parent.name:
            cleaned_path = cleaned_path.parent

        return cleaned_path.as_posix().replace("-", "_")

    def source_to_xml_for_index(self, base_uri: str, root_dir: Path) -> ET.Element:
        SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
        GEOCONNEX_NS = "https://geoconnex.us"
        last_modified = datettime_to_sitemap_iso_format(self.last_modified)

        # Root element with namespaces
        sitemap_el = ET.Element(
            f"{{{SITEMAP_NS}}}sitemap",
        )
        ET.indent(sitemap_el, space=" ", level=0)
        sitemap_location = self.canonical_sitemap_name(root_relative_dir=root_dir)

        # loc
        loc = ET.SubElement(sitemap_el, f"{{{SITEMAP_NS}}}loc")
        loc.text = f"{base_uri}/sitemap/{sitemap_location}.xml"

        # lastmod
        lastmod = ET.SubElement(sitemap_el, f"{{{SITEMAP_NS}}}lastmod")
        lastmod.text = last_modified

        # sitemap_id
        sitemap_id = ET.SubElement(sitemap_el, f"{{{GEOCONNEX_NS}}}sitemap_id")
        sitemap_id.text = sitemap_location.replace("/", ":")

        # metadata fields (safe escaping handled automatically)
        for key, value in self.metadata.items():
            el = ET.SubElement(sitemap_el, f"{{{GEOCONNEX_NS}}}{key}")
            el.text = "" if value is None else str(value)

        return sitemap_el


def get_all_sitemap_sources(root_dir: Path) -> list[SitemapSourceWithMetadata]:
    """
    Given a root dir, iterate through it recursively, finding all files
    ending with *.csv and returning metadata about them. All metadata files
    are stored in a parallel file named metadata.json in the same directory.

    If there are multiple csv files with one metadata.json, they share the
    same metadata info

    :param root_dir: `Path` of the root directory to search

    :returns: `list` of `CsvWithMetadata`
    """
    results: list[SitemapSourceWithMetadata] = []

    # Cache metadata per directory so we only read each metadata.json once
    metadata_cache: dict[Path, dict] = {}

    for file_path in root_dir.rglob("*.csv"):
        if file_path.parent not in metadata_cache:
            metadata_file = file_path.parent / "metadata.json"
            if metadata_file.exists():
                metadata_cache[file_path.parent] = json.loads(metadata_file.read_text())

            metadata = json.loads(metadata_file.read_text())
            if metadata.get("bulk_container_image"):
                results.append(
                    SitemapSourceWithMetadata(
                        last_modified=datetime.datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ),
                        metadata=metadata,
                        path=file_path,
                        file_type="bulk",
                    )
                )
                continue

        results.append(
            SitemapSourceWithMetadata(
                last_modified=datetime.datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ),
                metadata=metadata_cache.get(file_path.parent) or {},
                path=file_path,
                file_type="regex_csv" if is_regex_csv(file_path) else "one_to_one_csv",
            )
        )

    for file_path in root_dir.rglob("*.xml"):
        if file_path.parent not in metadata_cache:
            metadata_file = file_path.parent / "metadata.json"
            if metadata_file.exists():
                metadata_cache[file_path.parent] = json.loads(metadata_file.read_text())
        results.append(
            SitemapSourceWithMetadata(
                last_modified=datetime.datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ),
                metadata=metadata_cache.get(file_path.parent) or {},
                path=file_path,
                file_type="pregenerated_xml",
            )
        )

    return results


def OPTION_VERBOSITY(f):
    logging_options = ["ERROR", "WARNING", "INFO", "DEBUG"]
    log_format = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%SZ"

    def callback(ctx, param, value):
        if value is not None:
            logging.basicConfig(
                level=value, datefmt=date_format, format=log_format, stream=sys.stdout
            )
        return True

    return click.option(
        "--verbosity",
        "-v",
        type=click.Choice(logging_options),
        help="Verbosity",
        default="DEBUG",
        callback=callback,
    )(f)
