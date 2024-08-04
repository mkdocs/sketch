from .handlers.base import Handler
from .handlers.files import StaticFilesHandler
from .handlers.navigation import NavigationHandler
from .handlers.pages import PagesHandler
from .site import Site
from .utils import merge_dict, load_yaml

from typing import Optional, List
import click
import flask
import os


DIRECTORY = os.path.dirname(__file__)

DEFAULT_CONFIG = {
    'site_name': '',
    'build': {
        'url': '/',
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
        config = merge_dict(DEFAULT_CONFIG, config)
        self._url = config['build']['url']
        self._name = config['site_name']
        self._context = config['context']
        self._handlers = self.setup_handlers(config)

    def setup_handlers(self, config: dict) -> List[Handler]:
        return [
            StaticFilesHandler(config),
            PagesHandler(config),
            NavigationHandler(config)
        ]

    def initialize(self) -> Site:
        site = Site(url=self._url, name=self._name, context=self._context)
        for handler in self._handlers:
            handler.initialize(site)
        return site

    def build(self, site: Site) -> None:
        for handler in self._handlers:
            handler.build(site)

    def serve(self, site: Site, url: str) -> Optional[flask.Response]:
        for handler in self._handlers:
            response = handler.serve(site, url)
            if response is not None:
                return response


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

    app = flask.Flask(__name__)

    @app.route('/')
    @app.route('/<path:path>')
    def endpoint(path=''):
        url = f'/{path}'
        response = md.serve(site, url)
        if response is None:
            flask.abort(404)
        return response

    app.run()
