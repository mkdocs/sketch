from .base import Handler
from ..site import Navigation, NavItem, Pages, Site
from typing import List, Optional, Tuple
import flask


class NavigationHandler(Handler):
    def __init__(self, config: dict) -> None:
        self._nav_config = config["nav"]

    def initialize(self, site: Site) -> None:
        nav_items, _ = self._load_navigation(self._nav_config, site.pages)
        site.navigation = Navigation(nav_items)

    def build(self, site: Site) -> None:
        pass

    def serve(self, site: Site, url: str) -> Optional[flask.Response]:
        pass

    # ...

    def _load_navigation(
        self,
        config: list,
        pages: Pages,
        level: int = 1,
        parent: Optional[NavItem] = None,
        current: Optional[NavItem] = None,
    ) -> Tuple[list[NavItem], Optional[NavItem]]:
        nav_items: list[NavItem] = []
        for item in config:
            assert isinstance(item, dict)
            assert len(item) == 1
            key = list(item.keys())[0]
            value = item[key]
            if isinstance(value, list):
                # If the value is a list, it is a header.
                # TODO: Some headers have index pages associated with them.
                header = NavItem(
                    title=key,
                    level=level,
                    parent=parent,
                )
                nav_items.append(header)
                _, current = self._load_navigation(value, pages, level + 1, parent=header, current=current)
            elif isinstance(value, str):
                # TODO: error if page does not exist.
                referenced = pages.lookup_path(value)
                url = '' if referenced is None else referenced.url

                nav = NavItem(
                    title=key,
                    level=level,
                    page=referenced,
                    url=url,
                    parent=parent,
                    previous=current,
                    next=None,
                )
                nav_items.append(nav)
                if parent is not None:
                    parent.children.append(nav)
                if current is not None:
                    current.next = nav
                # Link the referenced page back to the navigation item.
                if referenced is not None:
                    referenced.navigation = nav
                current = nav
        return nav_items, current
