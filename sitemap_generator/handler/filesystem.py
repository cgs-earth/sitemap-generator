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

from datetime import datetime as dt
from git import Repo
import logging
import os
from pathlib import Path

from sitemap_generator.handler.base import BaseHandler, SITEMAP_DIR
from sitemap_generator.util import walk_path, parse

LOGGER = logging.getLogger(__name__)

# Environment Vars for Git Repository to source last mod
SOURCE_REPO = os.environ.get('SOURCE_REPO', '/geoconnex.us')
SOURCE_REPO_PATH = os.environ.get('SOURCE_REPO_PATH', 'namespaces')


class FileSystemHandler(BaseHandler):
    def __init__(self, filepath: Path, uri_stem: str) -> None:
        """
        Sitemap handler initializer

        :param filepath: `Path` of filepath to handle
        :param uri_stem: `str` of sitemap location

        :returns: `None`
        """
        super().__init__(str(filepath), uri_stem)
        # Git Repository objects
        self.repo = Repo(SOURCE_REPO)
        self.tree = self.repo.heads.master.commit.tree
        self.namespace = self.tree / SOURCE_REPO_PATH

    def handle(self) -> None:
        """
        Handle sitemap creation sitemapindex

        :returns: `None`
        """
        LOGGER.debug('Making urlsets')
        [self.make_urlset(file)
         for file in walk_path(self.root_path, r'.*.csv')]

        LOGGER.debug('Making sitemap index')
        urlsets = walk_path(self.root_path, r'.*.xml')
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
        Gets relative path to file.

        :param filename: `Path` of file

        :returns file_time: `str` of file lastmod as W3C Datetime
        """
        try:
            LOGGER.debug(f'Getting filetime from Git commit for {filename}')
            relative_path = self.get_rel_path(filename)
            blob = (self.namespace / relative_path / filename.name)
            commits = self.repo.iter_commits(paths=blob.path, max_count=1)
            commit = next(commits)
            file_time = commit.committed_datetime

        except KeyError as err:
            LOGGER.warning(err)
            _ = os.path.getmtime(filename)
            file_time = dt.fromtimestamp(_)

        except OSError as err:
            LOGGER.warning(err)
            file_time = dt.now()

        return file_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    def get_rel_path(self, filename: Path) -> str:
        """
        Gets relative path to file.

        :param filename: `Path` of file

        :returns parent: `str` of parent path
        """
        full_path = str(filename.resolve())
        LOGGER.debug(f'Resolving relative path for {full_path}')
        if self.root_path in full_path:
            LOGGER.debug('File in namespaces context')
            parent = filename.parent.relative_to(self.root_path)
        else:
            LOGGER.debug('File in sitemap context')
            parent = filename.parent.relative_to(SITEMAP_DIR)

        LOGGER.debug(f'Parent dir of file is: {parent}')
        return str(parent)
