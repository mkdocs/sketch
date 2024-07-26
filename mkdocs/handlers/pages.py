import os
from contextlib import contextmanager
from typing import Iterator, List, Optional


import flask
import jinja2
import markdown
import markdown_gfm_admonition
from mdx_linkify.mdx_linkify import LinkifyExtension
import slugify
import xml.etree.ElementTree as etree

from ..site import Pages, Page, Section, Site
from ..utils import list_files_within_directory, url_for_path


class BuildState:
    @contextmanager
    def active_page(self, page: Page) -> Iterator[None]:
        self.current_page = page
        if page.navigation is not None:
            for nav in page.navigation.breadcrumbs:
                nav.is_active = True
        try:
            yield
        finally:
            del(self.current_page)
            if page.navigation is not None:
                for nav in page.navigation.breadcrumbs:
                    nav.is_active = False


class PagesHandler:
    def __init__(self, config: dict) -> None:
        self._base_url = config['build']['url']
        self._docs_dir = config['directories']['docs']
        self._templates_dir = config['directories']['templates']
        self._build_dir = config['directories']['build']

    def initialize(self, site: Site) -> None:
        pages = []
        for path in list_files_within_directory(self._docs_dir):
            output_path = self._build_path(path)
            url = url_for_path(output_path, base_url=self._base_url)
            page = Page(
                url=url,
                path=path,
                context={},
                sections=[]
            )
            pages.append(page)

        pages = sorted(pages, key=lambda page: page.url)
        site.pages = Pages(pages)

    def build(self, site: Site) -> None:
        state = BuildState()
        template_env = self._setup_template_env(site)
        markdown_env = self._setup_markdown_env(site, state)
        for page in site.pages:
            with state.active_page(page):
                self._build_page(page, site, template_env, markdown_env)

    def serve(self, site: Site, url: str) -> Optional[flask.Response]:
        page = site.pages.lookup_url(url)
        if page is None:
            return None

        state = BuildState()
        template_env = self._setup_template_env(site)
        markdown_env = self._setup_markdown_env(site, state)
        return self._serve_page(state, page, site, template_env, markdown_env)

    # ...

    def _setup_template_env(self, site: Site) -> jinja2.Environment:
        # TODO: Lookup file and error if not found.
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._templates_dir),
        )
        template_env.filters['url'] = lambda path: os.path.join(site.url, path)
        return template_env

    def _setup_markdown_env(self, site: Site, state: BuildState) -> markdown.Markdown:
        markdown_env = markdown.Markdown(extensions=[
            # Handle triple backtick fenced code blocks.
            'fenced_code',
            # Tables. Obviously.
            'tables',
            # Add hyperlinks to URLs in the text.
            LinkifyExtension()
        ])

        # Deal with rewriting URLs in the markdown, to point to the build URLs.
        markdown_env.treeprocessors.register(
            item=_URLsProcessor(site, state),
            name='urls',
            priority=10,
        )

        # Annotate the page with sections information, for rendering a table of contents.
        markdown_env.treeprocessors.register(
            item=_SectionsProcessor(state),
            name='sections',
            priority=10,
        )

        # Support github-flavored "note", "tip", "information", "warning", "caution" blocks.
        markdown_env.parser.blockprocessors.register(
            item=markdown_gfm_admonition.GfmAdmonitionProcessor(markdown_env.parser),
            name='gfm_admonition',
            priority=105
        )
        return markdown_env

    def _build_path(self, source: str) -> str:
        """
        Convert the source path into a destination path.

        source            destination                url
        ------------------------------------------------------------
        index.md         | index.html               | /
        about.md         | about/index.html         | about/
        example/index.md | example/index.html       | example/
        example/topic.md | example/topic/index.html | example/topic/
        """
        dirname, basename = os.path.split(source)
        (root, ext) = os.path.splitext(basename)
        if root == 'index':
            return os.path.join(dirname, 'index.html')
        return os.path.join(dirname, root, 'index.html')

    def _build_page(self, page: Page, site: Site, template_env: jinja2.Environment, markdown_env: markdown.Markdown) -> None:
        input_rel_path = page.path
        output_rel_path = self._build_path(input_rel_path)

        print(f'Build {input_rel_path!r} -> {output_rel_path!r}')
        input_path = os.path.join(self._docs_dir, input_rel_path)
        output_path = os.path.join(self._build_dir, output_rel_path)

        with open(input_path, "r") as input_file:
            input_text = input_file.read()

        page.text = input_text
        page.html = markdown_env.convert(input_text)

        template = template_env.get_template("base.html")
        output_text = template.render({
            "site": site,
            "page": page
        })

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as output_file:
            output_file.write(output_text)

    def _serve_page(self, state: BuildState, page: Page, site: Site, template_env: jinja2.Environment, markdown_env: markdown.Markdown) -> flask.Response:
        source = os.path.join(self._docs_dir, page.path)

        with open(source, "r") as input_file:
            input_text = input_file.read()

        with state.active_page(page):
            page.text = input_text
            page.html = markdown_env.convert(input_text)

            template = template_env.get_template("base.html")
            content = template.render({
                "site": site,
                "page": page
            })

        return flask.make_response(content)


class _URLsProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, site: Site, state: BuildState) -> None:
        self._site = site
        self._state = state

    def run(self, root: etree.Element) -> etree.Element:
        for element in root.iter():
            if element.tag == 'a':
                key = 'href'
            elif element.tag == 'img':
                key = 'src'
            else:
                continue

            url_or_path = element.get(key)
            if url_or_path is not None:
                output_url = self.rewrite_url(url_or_path)
                element.set(key, output_url)

        return root

    def rewrite_url(self, url_or_path: str) -> str:
        # TODO: Improve
        if url_or_path.startswith('http://') or url_or_path.startswith('https://'):
            return url_or_path

        current_page = self._state.current_page
        current_directory = os.path.dirname(current_page.path)

        referenced_path = os.path.normpath(os.path.join(current_directory, url_or_path))
        referenced_page = self._site.pages.lookup_path(referenced_path)
        if referenced_page is None:
            return "#"
        return referenced_page.url


class _SectionsProcessor(markdown.treeprocessors.Treeprocessor):
    """
    This processor does exactly two things:

    * Annotate headers with an 'id' attribute,
      which will be present in the output HTML.
    * Annotate the current page with a 'sections' attribute,
      which can be used to render a table of contents.
    """

    # TODO:
    #
    # We would also like to save the 'text' attribute to sections,
    # so that we can use them to generate search indexes.
    #
    # The 'fenced_code' extension is a bit awkward for us here,
    # as it hides the content of the code blocks into an html stash.
    #
    # Useful pointers...
    #
    # HashHeaderProcessor, SetextHeaderProcessor
    # BacktickInlineProcessor(BACKTICK_RE), 'backtick', 190)
    # RawHtmlPostprocessor

    def __init__(self, state: BuildState):
        self._state = state

    def run(self, root: etree.Element) -> etree.Element:
        # A function that creates unique ascii identifiers from the section titles,
        # suitable for usage as HTML id attributes.
        title_to_id = slugify.UniqueSlugify(to_lower=True)

        sections = []
        for element in root.iter():
            if element.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                level = int(element.tag[1])
                title = ''.join(element.itertext())
                id = title_to_id(title)

                # Update the element with an ID attribute.
                element.set('id', id)
                sections.append(Section(
                    title=title,
                    id=id,
                    level=level
                ))

        # Set the sections on the current page, as a side-effect.
        self._state.current_page.sections = sections
        return root
