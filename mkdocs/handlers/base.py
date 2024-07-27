from ..site import Site
import flask


class Handler:
    def initialize(self, site: Site) -> None:
        pass

    def build(self, site: Site) -> None:
        pass

    def serve(self, site: Site, url: str) -> flask.Response:
        pass
