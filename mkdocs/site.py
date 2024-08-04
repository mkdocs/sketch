from dataclasses import dataclass, field
from typing import Any, Iterator, Optional


# Static Files

@dataclass
class Files:
    all: list["File"] = field(default_factory=list)

    # We'll want to provide this to support the 'url' template tag.
    # Ie... Make sure we can warn on `{{ "css/does_not_exist.css"|url }}`
    #
    # def lookup(self, path: str) -> Optional[Page]:
    #     for page in self.all:
    #         if page.path == path:
    #             return page

    def lookup_url(self, url: str) -> Optional["File"]:
        for file in self.all:
            if file.url == url:
                return file
        return None

    def __iter__(self) -> Iterator["File"]:
        return iter(self.all)

    def __len__(self) -> int:
        return len(self.all)

    def __repr__(self) -> str:
        return f"Files({self.all!r})"


@dataclass
class File:
    url: str
    path: str

    def __repr__(self) -> str:
        return f"File({self.path!r})"


# Pages

@dataclass
class Pages:
    all: list["Page"] = field(default_factory=list)

    def lookup_url(self, url: str) -> Optional["Page"]:
        for page in self.all:
            if page.url == url:
                return page
        return None

    def lookup_path(self, path: str) -> Optional["Page"]:
        for page in self.all:
            if page.path == path:
                return page
        return None

    def __iter__(self) -> Iterator["Page"]:
        return iter(self.all)

    def __len__(self) -> int:
        return len(self.all)

    def __repr__(self) -> str:
        return f"Pages({self.all!r})"


@dataclass
class Page:
    url: str
    path: str

    context: dict = field(default_factory=dict)
    sections: list["Section"] = field(default_factory=list)
    navigation: Optional["NavItem"] = None

    @property
    def is_homepage(self) -> bool:
        return self.url == "/"

    def __repr__(self) -> str:
        return f"Page({self.path!r})"


@dataclass
class Section:
    title: str
    id: str
    level: int

    def __repr__(self) -> str:
        return f"Section({self.title!r}, level={self.level})"


# Navigation

@dataclass
class Navigation:
    all: list["NavItem"] = field(default_factory=list)

    def __iter__(self) -> Iterator["NavItem"]:
        return iter(self.all)

    def __len__(self) -> int:
        return len(self.all)

    def __repr__(self) -> str:
        return f"Navigation({self.all!r})"


@dataclass
class NavItem:
    title: str
    level: int
    url: str = ""

    page: Optional["Page"] = None

    # relationships
    parent: Optional["NavItem"] = None
    previous: Optional["NavItem"] = None
    next: Optional["NavItem"] = None
    children: list["NavItem"] = field(default_factory=list)

    # state indicating if the navigation item is "active"
    # ie. either the current page or one of its ancestors.
    is_active = False

    @property
    def breadcrumbs(self) -> list["NavItem"]:
        # Returns nav and all its ancestors,
        # ordered with the root first.
        breadcrumbs = [self]
        current = self
        while current.parent:
            current = current.parent
            breadcrumbs.append(current)
        return list(reversed(breadcrumbs))

    def __repr__(self) -> str:
        if self.children:
            return f"NavItem({self.title!r}, children={self.children!r})"
        return f"NavItem({self.title!r})"


# Site

@dataclass
class Site:
    url: str
    name: str
    context: dict
    pages: "Pages" = field(default_factory=Pages)
    files: "Files" = field(default_factory=Files)
    navigation: "Navigation" = field(default_factory=Navigation)
