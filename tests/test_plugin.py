import os
import tempfile
import mkdocs
from mkdocs.config import Config
from mkdocs.structure.files import File
import unittest
from mkdocs.structure.pages import Page
from yaml import dump


DEFAULT_CONFIG = {
    "site_name": 'My Site',
    "plugins": [
        {
            "render_swagger": {}
        },
    ],
}


def render_markdown(markdown, config_options=None):
    # Create a temporary directory for the Mkdocs site
    config_options = config_options or {}
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock Mkdocs config
        config = Config([])
        config.load_dict(dict(
            site_name='My Site',
            theme={
                'name': 'mkdocs',
                'custom_dir': 'custom_theme',
                'static_templates': ['404.html']
            },
            extra_javascript=[js] if (
                js := config_options.pop('extra_javascript', None)) else [],
            extra_css=[css] if (
                css := config_options.pop('extra_css', None)) else [],
            plugins=[{'render_swagger': config_options or {}}],
        ))

        # Create a mock Mkdocs page
        page = Page(title='My Page', file=File(
            'my_page.md', temp_dir, temp_dir, False), config=config)

        # # Create a mock Mkdocs TOC
        # toc = Toc([
        #     {'title': 'Home', 'url': 'index.html', 'children': []},
        #     {'title': 'My Page', 'url': 'my_page.html', 'children': []}
        # ])

        # Create a mock Mkdocs files collection
        files = {
            'index.md': '',
            'my_page.md': markdown
        }

        # # Create a mock Mkdocs site navigation
        # nav = mkdocs.structure.nav.Navigation(
        #     pages=[page],
        #     config=config,
        #     files=files,
        #     toc=toc
        # )

        # Create a mock Mkdocs site
        site = mkdocs.structure.site.Site(
            config=config,
            files=files,
            pages=[page],
            nav=nav,
            theme=mkdocs.themes.get_theme_instance(config),
            template_context={},
            use_directory_urls=False
        )

        # Build the Mkdocs site
        mkdocs.commands.build.build(config, dump_config=False, clean_site_dir=False,
                                    strict=False, use_directory_urls=False, site_dir=temp_dir)

        # Render the page and return the HTML output
        with open(os.path.join(temp_dir, page.url), 'r') as f:
            html = f.read()

    return html

class SwaggerPluginTestCase(unittest.TestCase):
    def test_sanity(self):
        result = render_markdown("")

