import os
import shutil
from typing import List

from .base import Handler
from ..site import File, Files, Site
from ..utils import list_files_within_directory, url_for_path

from starlette.routing import Route
from starlette.responses import FileResponse


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

    def routes(self, site: Site) -> List[Route]:
        routes = []
        for file in site.files:
            route = self._route_for_file(file)
            routes.append(route)
        return routes

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

    def _route_for_file(self, file: File) -> Route:
        source = os.path.join(self._statics_dir, file.path)
        return Route(file.url, endpoint=FileResponse(source), methods=['GET'])
