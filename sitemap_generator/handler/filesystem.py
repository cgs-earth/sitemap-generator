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

from datetime import datetime as dt, timezone
import logging
from pathlib import Path

from sitemap_generator.handler.base import BaseHandler
from sitemap_generator.util import walk_path, parse

LOGGER = logging.getLogger(__name__)

class FileSystemHandler(BaseHandler):
    def __init__(
        self, namespace_dir: Path, uri_stem: str, sitemap_output_dir: Path
    ) -> None:
        """
        Sitemap handler initializer

        :param input_dir: `Path` of input directory with the namespaces
        :param uri_stem: `str` of sitemap location
        :param sitemap_output_dir: `Path` in which the generated xml will be stored

        :returns: `None`
        """
        super().__init__(namespace_dir, uri_stem, sitemap_output_dir)

    def generate(self) -> None:
        """
        Generate sitemap xml files

        :returns: `None`
        """
        LOGGER.debug('Making urlsets')
        [self.make_urlset(file)
         for file in walk_path(self.repo, r'.*.csv')]

        LOGGER.debug('Making sitemap index')
        urlsets = walk_path(self.repo, r'.*.xml')
        self.make_sitemap(urlsets)

        LOGGER.debug('Finished task')

    def parse(self, filename: Path, n: int = 50000) -> list:
        """
        Parses file to a CSV

        :param filename: `Path` of source file to parse
        :param n: `int` size of each chunk

        :returns: `list`
        """
        return parse(filename, n)

    def get_filetime(self, filename: Path) -> str:
        """
        Gets last modified time of a file.

        :param filename: Path of file
        :returns: file time as W3C datetime (UTC ISO 8601)
        """
        LOGGER.debug(f"Getting filetime from filesystem for {filename}")
        timestamp = filename.stat().st_mtime
        file_time = dt.fromtimestamp(timestamp, tz=timezone.utc)
        return file_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_rel_path(self, filename: Path) -> str:
        """
        Gets relative path to file.

        :param filename: `Path` of file

        :returns parent: `str` of parent path
        """
        full_path = filename.resolve()
        LOGGER.debug(f'Resolving relative path for {full_path}')
        if self.repo.as_posix() in full_path.as_posix():
            LOGGER.debug('File in namespaces context')
            parent = filename.parent.relative_to(self.repo)
        else:
            LOGGER.debug('File in sitemap context')
            parent = filename.parent.relative_to(self.sitemap_output_dir)

        LOGGER.debug(f'Parent dir of file is: {parent}')
        return str(parent)
