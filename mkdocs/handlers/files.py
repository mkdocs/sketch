import os
import shutil
from typing import List, Optional

from .base import Handler
from ..site import File, Files, Site
from ..utils import list_files_within_directory, url_for_path

import flask


class StaticFilesHandler(Handler):
    def __init__(self, config: dict) -> None:
        self._base_url = config['build']['url']
        self._statics_dir = config['directories']['statics']
        self._build_dir = config['directories']['build']

    def initialize(self, site: Site):
        files = []
        for path in list_files_within_directory(self._statics_dir):
            url = url_for_path(path, base_url=self._base_url)
            file = File(url=url, path=path)
            files.append(file)

        files = sorted(files, key=lambda file: file.url)
        site.files = Files(files)

    def build(self, site: Site) -> None:
        for file in site.files:
            self._build_file(file)

    def serve(self, site: Site, url: str) -> Optional[flask.Response]:
        file = site.files.lookup_url(url)
        if file is not None:
            return self._serve_file(file)

    # ...

    def _build_file(self, file: File) -> None:
        source = os.path.join(self._statics_dir, file.path)
        path = os.path.join(self._build_dir, file.path)

        print(f'Copy {source!r} -> {path!r}')
        self._make_parent_directories(path)
        shutil.copy(source, path)

    def _make_parent_directories(self, path: str) -> None:
        """
        Create all parent directories to the given path, if they do not yet exist.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def _serve_file(self, file: File) -> flask.Response:
        source = os.path.join(self._statics_dir, file.path)
        return flask.send_file(source)
