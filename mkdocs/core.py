from .handlers.files import StaticFilesHandler
from .handlers.navigation import NavigationHandler
from .handlers.pages import PagesHandler
from .site import Site
from .utils import merge_dict, load_yaml

from typing import List
from starlette.routing import Route
from starlette.applications import Starlette
import click
import uvicorn
import os


DIRECTORY = os.path.dirname(__file__)

DEFAULT_CONFIG = {
    'build': {
        'url': '/'
    },
    'directories': {
        'docs': 'docs',
        'statics': os.path.join(DIRECTORY, 'statics'),
        'templates': os.path.join(DIRECTORY, 'templates'),
        'build': 'site'
    },
    'context': {},
}


class MkDocs:
    def __init__(self, config: dict) -> None:
        config = merge_dict(config, DEFAULT_CONFIG)
        self._url = config['build']['url']
        self._context = config['context']
        self._handlers = [
            StaticFilesHandler(config),
            PagesHandler(config),
            NavigationHandler(config)
        ]

    def initialize(self) -> Site:
        site = Site(url=self._url, context=self._context)
        for handler in self._handlers:
            handler.initialize(site)
        return site

    def build(self, site: Site) -> None:
        for handler in self._handlers:
            handler.build(site)

    def serve(self, site: Site):
        routes: List[Route] = []
        for handler in self._handlers:
            routes.extend(handler.routes(site))
        app = Starlette(debug=True, routes=routes)
        uvicorn.run(app)


@click.group()
def cli():
    pass

@cli.command()
def build():
    config = load_yaml("mkdocs.yml")
    md = MkDocs(config)
    site = md.initialize()
    md.build(site)

@cli.command()
def serve():
    config = load_yaml("mkdocs.yml")
    md = MkDocs(config)
    site = md.initialize()
    md.serve(site)
