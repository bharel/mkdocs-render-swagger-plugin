import os
import shutil
import tempfile
import unittest
from yaml import dump
import pathlib
import subprocess
import render_swagger
import unittest.mock
from mkdocs.structure.pages import Page
from typing import Optional
from mkdocs.structure.files import File

DEFAULT_CONFIG = {
    "site_name": 'My Site',
    "plugins": [
        {
            "render_swagger": {}
        },
    ],
}


def render_markdown(markdown: str, config_options: Optional[dict] = None
                    ) -> str:
    """Render a Markdown string using Mkdocs.

    Args:
        markdown: The Markdown to render.
        config_options: A dictionary of Mkdocs config options.

    Returns:
        The rendered HTML.
    """
    # Create a temporary directory for the Mkdocs site
    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = pathlib.Path(temp_dir)

        # Create a mock Mkdocs docs directory
        docs = temp_dir / "docs"
        docs.mkdir(exist_ok=True)

        # Create a mock Mkdocs config
        config = DEFAULT_CONFIG.copy()
        if config_options:
            config["plugins"][0]["render_swagger"].update(config_options)

        with (temp_dir / "mkdocs.yml").open("w") as f:
            dump(config, f)

        # Create a mock Markdown file
        with (docs / "index.md").open("w") as f:
            f.write(markdown)

        # Copy all samples to the mock docs directory
        samples = pathlib.Path(__file__).parent / "samples"
        shutil.copytree(samples, docs, dirs_exist_ok=True)

        # Run Mkdocs
        process = subprocess.run(["mkdocs", "build"], cwd=temp_dir,
                                 capture_output=True)
        assert process.returncode == 0, process.stderr.decode()

        # Read the rendered HTML
        return (temp_dir / "site" / "index.html").read_text()


class FullRenderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cwd = pathlib.Path(__file__).parent
        cls.old_cwd = pathlib.Path.cwd()
        os.chdir(cwd)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.old_cwd)

    def test_sanity(self):
        result = render_markdown(r"!!swagger openapi_3.0.yml!!")
        expected = """<p><link type="text/css" rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"></p>
<div id="swagger-ui-1">
</div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" charset="UTF-8"></script>
<script>
    SwaggerUIBundle({
      url: 'openapi_3.0.yml',
      dom_id: '#swagger-ui-1',
    })
</script>""".strip()  # noqa: E501
        self.assertIn(expected, result)

    def test_sanity_http(self):
        result = render_markdown(
            r"!!swagger-http https://petstore.swagger.io/v2/swagger.json!!")
        expected = """<p><link type="text/css" rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"></p>
<div id="swagger-ui-1">
</div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" charset="UTF-8"></script>
<script>
    SwaggerUIBundle({
      url: 'https://petstore.swagger.io/v2/swagger.json',
      dom_id: '#swagger-ui-1',
    })
</script>""".strip()  # noqa: E501
        self.assertIn(expected, result)

    def test_sanity_http_with_config(self):
        result = render_markdown(
            r"!!swagger-http https://petstore.swagger.io/v2/swagger.json!!",
            config_options={
                "javascript":
                    "https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js"  # noqa: E501
            }
        )

        expected = """<p><link type="text/css" rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"></p>
<div id="swagger-ui-1">
</div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
<script>
    SwaggerUIBundle({
      url: 'https://petstore.swagger.io/v2/swagger.json',
      dom_id: '#swagger-ui-1',
    })
</script>""".strip()  # noqa: E501
        self.assertIn(expected, result)


class SwaggerPluginTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cwd = pathlib.Path(__file__).parent
        cls.old_cwd = pathlib.Path.cwd()
        os.chdir(cwd)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.old_cwd)

    def setUp(self):
        self.plugin = render_swagger.SwaggerPlugin()
        self.config = render_swagger.SwaggerConfig()
        self.page = Page("index.md", File("index.md", "samples",
                                          "samples", False),
                         {})
        self._id_patcher = unittest.mock.patch(
            'render_swagger.generate_id', return_value="swagger-ui")
        self.generate_id = self._id_patcher.start()

    def tearDown(self):
        self._id_patcher.stop()

    def setConfig(self, config=None):
        config = config or {}
        self.plugin.load_config(options=config)
        self.plugin.on_config({})

    def test_sanity(self):
        self.setConfig({})
        files = []
        result = self.plugin.on_page_markdown(
            r"!!swagger openapi_3.0.yml!!", self.page, DEFAULT_CONFIG, files)
        expected = render_swagger.TEMPLATE.substitute(
            path="openapi_3.0.yml",
            swagger_lib_css=render_swagger.DEFAULT_SWAGGER_LIB['css'],
            swagger_lib_js=render_swagger.DEFAULT_SWAGGER_LIB['js'],
            id="swagger-ui")
        self.assertEqual(expected.strip(), result.strip())

    def test_sanity_http(self):
        self.setConfig({})
        result = self.plugin.on_page_markdown(
            r"!!swagger-http https://petstore.swagger.io/v2/swagger.json!!",
            self.page, DEFAULT_CONFIG, [])
        expected = render_swagger.TEMPLATE.substitute(
            path="https://petstore.swagger.io/v2/swagger.json",
            swagger_lib_css=render_swagger.DEFAULT_SWAGGER_LIB['css'],
            swagger_lib_js=render_swagger.DEFAULT_SWAGGER_LIB['js'],
            id="swagger-ui")
        self.assertEqual(expected.strip(), result.strip())

    def test_javascript_config(self):
        self.setConfig({
            "javascript": "https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js"  # noqa: E501
        })
        result = self.plugin.on_page_markdown(
            r"!!swagger-http https://petstore.swagger.io/v2/swagger.json!!",
            self.page, DEFAULT_CONFIG, [])
        expected = render_swagger.TEMPLATE.substitute(
            path="https://petstore.swagger.io/v2/swagger.json",
            swagger_lib_css=render_swagger.DEFAULT_SWAGGER_LIB['css'],
            swagger_lib_js="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js",  # noqa: E501
            id="swagger-ui")
        self.assertEqual(expected.strip(), result.strip())

    def test_css_config(self):
        self.setConfig({
            "css": "https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css"  # noqa: E501
        })
        result = self.plugin.on_page_markdown(
            r"!!swagger-http https://petstore.swagger.io/v2/swagger.json!!",
            self.page, DEFAULT_CONFIG, [])
        expected = render_swagger.TEMPLATE.substitute(
            path="https://petstore.swagger.io/v2/swagger.json",
            swagger_lib_css="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css",  # noqa: E501
            swagger_lib_js=render_swagger.DEFAULT_SWAGGER_LIB['js'],
            id="swagger-ui")
        self.assertEqual(expected.strip(), result.strip())

    def test_allow_arbitrary_locations(self):
        self.setConfig({
            "allow_arbitrary_locations": True
        })
        files = []
        result = self.plugin.on_page_markdown(
            r"!!swagger ../arbitrary_sample/openapi.yml!!",
            self.page, DEFAULT_CONFIG, files)
        expected = render_swagger.TEMPLATE.substitute(
            path="openapi.yml",
            swagger_lib_css=render_swagger.DEFAULT_SWAGGER_LIB['css'],
            swagger_lib_js=render_swagger.DEFAULT_SWAGGER_LIB['js'],
            id="swagger-ui")
        self.assertEqual(expected.strip(), result.strip())
        file_ = files[0]
        self.assertEqual(file_.abs_src_path,
                         os.path.join("arbitrary_sample", "openapi.yml"))
        self.assertEqual(file_.src_path, "openapi.yml")
        self.assertEqual(file_.abs_dest_path,
                         os.path.join("samples", "openapi.yml"))

    def test_disallow_arbitrary_locations(self):
        self.setConfig({
            "allow_arbitrary_locations": False
        })
        files = []
        result = self.plugin.on_page_markdown(
            r"!!swagger ../arbitrary_sample/openapi.yml!!",
            self.page, DEFAULT_CONFIG, files)
        self.assertIn("Arbitrary locations are not allowed ", result)

    def test_nonexisting_file(self):
        self.setConfig({})
        files = []
        result = self.plugin.on_page_markdown(
            r"!!swagger nonexisting.yml!!",
            self.page, DEFAULT_CONFIG, files)
        self.assertIn("File nonexisting.yml not found", result)

    def test_usage(self):
        self.setConfig({})
        files = []
        result = self.plugin.on_page_markdown(
            r"!!swagger!!",
            self.page, DEFAULT_CONFIG, files)
        self.assertIn("!! SWAGGER ERROR: Usage:", result)

    def test_two_files_same_name(self):
        self.setConfig({
            "allow_arbitrary_locations": True
        })
        files = [
            File("openapi.yml", "samples", "samples", False),
        ]
        result = self.plugin.on_page_markdown(
            r"!!swagger ../arbitrary_sample/openapi.yml!!",
            self.page, DEFAULT_CONFIG, files)
        self.assertIn("Cannot use 2 different swagger files", result)

    # Is this ok? It loads the JS and CSS twice.
    def test_two_swaggers_same_page(self):
        self.setConfig({
            "allow_arbitrary_locations": True
        })
        files = []
        self.generate_id.side_effect = ["swagger-ui-1", "swagger-ui-2"]
        result = self.plugin.on_page_markdown(
            "!!swagger openapi_3.0.yml!!\n"
            "\n!!swagger ../arbitrary_sample/openapi.yml!!",
            self.page, DEFAULT_CONFIG, files)
        expected = (render_swagger.TEMPLATE.substitute(
            path="openapi_3.0.yml",
            swagger_lib_css=render_swagger.DEFAULT_SWAGGER_LIB['css'],
            swagger_lib_js=render_swagger.DEFAULT_SWAGGER_LIB['js'],
            id="swagger-ui-1") +
            "\n\n" +
            render_swagger.TEMPLATE.substitute(
                path="openapi.yml",
                swagger_lib_css=render_swagger.DEFAULT_SWAGGER_LIB['css'],
                swagger_lib_js=render_swagger.DEFAULT_SWAGGER_LIB['js'],
                id="swagger-ui-2"))
        self.assertEqual(expected.strip(), result.strip())

    def test_backwards_compatability_js_css(self):
        self.plugin.load_config(options={})

        with self.assertWarns(FutureWarning) as cm:
            self.plugin.on_config({
                "extra_javascript": [
                    "unrelated.js", "test/swagger-ui-bundle.js"],
                "extra_css": ["unrelated.css", "test/swagger-ui.css"]})

        self.assertIn(
            "Please use the javascript configuration option for "
            "mkdocs-render-swagger-plugin instead of extra_javascript.",
            cm.warnings[0].message.args[0])

        self.assertIn(
            "Please use the css configuration option for "
            "mkdocs-render-swagger-plugin instead of extra_css.",
            cm.warnings[1].message.args[0])

        self.assertEqual(self.plugin.config.javascript,
                         "test/swagger-ui-bundle.js")
        self.assertEqual(self.plugin.config.css, "test/swagger-ui.css")


class SwaggerMiscTestCase(unittest.TestCase):
    def test_id_generation(self):
        self.assertNotEqual(render_swagger.generate_id(),
                            render_swagger.generate_id())
