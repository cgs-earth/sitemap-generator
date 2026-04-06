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
import logging
import os
from pathlib import Path
from shutil import copy2
from typing import Iterator

from sitemap_generator.util import (url_join, get_smi, add_smi_node,
                                    get_urlset, add_urlset_node,
                                    write_tree)

LOGGER = logging.getLogger(__name__)


class BaseHandler:
    """Sitemap Generator Handler"""

    sitemap_output_dir: Path

    def __init__(
        self,
        namespace_dir: Path,
        uri_stem: str,
        sitemap_output_dir: Path,
    ) -> None:
        """
        Sitemap handler initializer

        :param namespace_dir: `Path` of input directory to use for generation
        :param uri_stem: `str` of sitemap location
        :param sitemap_output_dir: `Path` in which the generated xml will be stored

        :returns: `None`
        """
        sitemap_dir_env = os.environ.get('SITEMAP_DIR')
        
        match (sitemap_output_dir, sitemap_dir_env):
            case (None, None) as _USE_DEFAULT_FALLBACK:
                self.sitemap_output_dir = Path(__file__).parent.parent
            case (None, _) as _USE_SITEMAP_DIR_ENV:
                self.sitemap_output_dir = Path(sitemap_output_dir)
            case (_, None) as _USE_SITEMAP_OUTPUT_DIR:
                self.sitemap_output_dir = sitemap_output_dir

        input_dir_env = os.environ.get("SOURCE_REPO_PATH")

        match (input_dir_env, namespace_dir):
            case (None, None) as _USE_DEFAULT_FALLBACK:
                self.repo = Path(__file__).parent.parent.parent / "geoconnex.us" / "namespaces"
            case (None, _) as _USE_FILEPATH:
                self.repo = namespace_dir
            case (_, _) as _USE_ENV:
                assert input_dir_env, "SOURCE_REPO_PATH environment variable not set;"
                " this must be set to the relative dir of a local git repository in order to generate sitemaps"
                self.repo = Path(input_dir_env)
        
        assert self.repo.is_dir(), (
            f"{self.repo=} must be a directory that exists"
        )

        self.uri_stem = uri_stem

    def generate(self) -> None:
        """
        Handle sitemap creation sitemapindex

        :returns: `None`
        """
        raise NotImplementedError

    def parse(self, filename: Path, n: int = 50000) -> list:
        """
        Parse sitemap creation sitemapindex

        :returns: `None`
        """
        raise NotImplementedError

    def get_filetime(self, filename: Path) -> str:
        """
        Gets relative path to file.

        :param filename: `Path` of file

        :returns file_time: `str` of file lastmod as W3C Datetime
        """
        raise NotImplementedError

    def get_rel_path(self, filename: Path) -> str:
        """
        Gets relative path to file.

        :param filename: `Path` of file

        :returns parent: `str` of parent path
        """
        raise NotImplementedError

    def make_urlset(self, filename: Path) -> None:
        """
        Create urlset from csv file.

        :param filename: `Path` of source file for urlset

        :returns: `None`
        """
        LOGGER.debug(f'Making urlset for {filename}')
        file_time = self.get_filetime(filename)
        urlsets = self.parse(filename)

        for i, chunk in enumerate(urlsets):
            # Build sitemaps for each csv file
            tree, root = get_urlset()
            for line in chunk:
                url_ = line[0]
                if '$' in url_:
                    LOGGER.warning(f'Regex detected in {filename}')
                    return
                add_urlset_node(root, url_, file_time)

            # Write sitemap.xml
            fidx = f'{filename.stem}__{i}'
            sitemap_file = (filename.parent / fidx).with_suffix('.xml')
            write_tree(tree, sitemap_file)

            _ = datetime.strptime(file_time, '%Y-%m-%dT%H:%M:%SZ')
            mtime = _.timestamp()
            atime = datetime.now().timestamp()
            os.utime(sitemap_file, (atime, mtime))

    def make_sitemap(self, files: Iterator[Path]) -> None:
        """
        Create sitemapindex

        :param files: `Iterator` of urlsets to index

        :returns: `None`
        """
        tree, root = get_smi()
        for f in files:
            LOGGER.debug(f'Processing urlset: {f.resolve()}')

            try:
                # Make sure file is sitemap
                int(f.stem.split('__').pop())
            except ValueError:
                LOGGER.error(f'Skipping {f.name}')
                continue

            # Move xml to /sitemaps
            filepath = (self.sitemap_output_dir / self.get_rel_path(f))
            filepath.mkdir(parents=True, exist_ok=True)
            file_path = filepath / f.name
            LOGGER.debug(f'Copying urlset to {filepath}')
            copy2(f, file_path)

            # create to link /sitemap/_sitemap.xml
            file_time = self.get_filetime(file_path)
            url_ = url_join(self.uri_stem, file_path)
            add_smi_node(root, url_, file_time)

        sitemap_out = self.sitemap_output_dir / '_sitemap.xml'
        LOGGER.debug(f'Writing sitemapindex to {sitemap_out}')
        write_tree(tree, sitemap_out)
