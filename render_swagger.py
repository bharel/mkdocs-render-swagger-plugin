import os
import re
import string
import urllib.parse
from pathlib import Path
from xml.sax.saxutils import escape

import mkdocs.plugins
from mkdocs.config import config_options
from mkdocs.config.base import Config as MkDocsConfig
from mkdocs.structure.files import File

__version__ = "0.1.2"

USAGE_MSG = (
    "Usage: '!!swagger <filename>!!' or '!!swagger-http <url>!!'. "
    "File must either exist locally and be placed next to the .md that "
    "contains the swagger statement, or be an http(s) URL.")

TEMPLATE = string.Template("""

<link type="text/css" rel="stylesheet" href="$swagger_lib_css">
<div id="$id">
</div>
<script src="$swagger_lib_js" charset="UTF-8"></script>
<script>
    SwaggerUIBundle({
      url: '$path',
      dom_id: '#$id',
    })
</script>

""")


def generate_id():
    generate_id.counter += 1
    return f"swagger-ui-{generate_id.counter}"


generate_id.counter = 0


ERROR_TEMPLATE = string.Template("!! SWAGGER ERROR: $error !!")

# Used for JS. Runs locally on end-user.
# RFI / LFI possible. Use with caution.
TOKEN = re.compile(r"!!swagger(?: (?P<path>[^\s<>&:!]+))?!!")

# HTTP(S) variant
TOKEN_HTTP = re.compile(r"!!swagger-http(?: (?P<path>https?://[^\s!]+))?!!")

DEFAULT_SWAGGER_LIB = {
    'css': "https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    'js': "https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"
}


def swagger_lib(config) -> dict:
    """
    Provides the actual swagger library used
    """
    lib_swagger = DEFAULT_SWAGGER_LIB.copy()
    extra_javascript = config.get('extra_javascript', [])
    extra_css = config.get('extra_css', [])
    for lib in extra_javascript:
        lib = str(lib)  # Can be an instance of ExtraScriptValue
        if os.path.basename(
                urllib.parse.urlparse(lib).path) == 'swagger-ui-bundle.js':
            import warnings
            warnings.warn(
                "Please use the javascript configuration option for "
                "mkdocs-render-swagger-plugin instead of extra_javascript.",
                FutureWarning)
            lib_swagger['js'] = lib
            break

    for css in extra_css:
        if os.path.basename(
                urllib.parse.urlparse(css).path) == 'swagger-ui.css':
            warnings.warn(
                "Please use the css configuration option for "
                "mkdocs-render-swagger-plugin instead of extra_css.",
                FutureWarning)
            lib_swagger['css'] = css
            break
    return lib_swagger


class SwaggerConfig(mkdocs.config.base.Config):
    javascript = config_options.Type(str, default="")
    css = config_options.Type(str, default="")
    allow_arbitrary_locations = config_options.Type(bool, default=False)


class SwaggerPlugin(mkdocs.plugins.BasePlugin[SwaggerConfig]):
    def on_config(self, config: MkDocsConfig, **kwargs):
        lib = swagger_lib(config)
        self.config.javascript = self.config.javascript or lib['js']
        self.config.css = self.config.css or lib['css']
        return config

    def on_page_markdown(self, markdown, page, config, files):
        is_http = False
        match = TOKEN.search(markdown)

        if match is None:
            match = TOKEN_HTTP.search(markdown)
            is_http = True

        if match is None:
            return markdown

        pre_token = markdown[:match.start()]
        post_token = markdown[match.end():]

        def _error(message):
            return (
                pre_token + escape(ERROR_TEMPLATE.substitute(error=message)) +
                post_token)

        path = match.group("path")

        if path is None:
            return _error(USAGE_MSG)

        if is_http:
            url = path
        else:
            if "/" in path or "\\" in path:
                if not self.config.allow_arbitrary_locations:
                    return _error(
                        "Arbitrary locations are not allowed due to RFI/LFI "
                        "security risks. "
                        "Please enable the 'allow_arbitrary_locations' "
                        "configuration option to allow this.")
            try:
                api_file = Path(page.file.abs_src_path).parent / path
            except ValueError as exc:  # pragma: no cover
                return _error(f"Invalid path. {exc.args[0]}")

            if not api_file.exists():
                return _error(f"File {path} not found.")

            src_dir = api_file.parent
            dest_dir = Path(page.file.abs_dest_path).parent

            new_file = File(api_file.name, src_dir, dest_dir, False)
            url = Path(new_file.abs_dest_path).name

            if any(f.abs_src_path != new_file.abs_src_path and
                   f.dest_uri == new_file.dest_uri for f in files):
                return _error("Cannot use 2 different swagger files with "
                              "same filename in same page.")

            files.append(new_file)

        markdown = pre_token + TEMPLATE.substitute(
            path=url, swagger_lib_js=self.config.javascript,
            swagger_lib_css=self.config.css, id=generate_id()
        ) + post_token

        # If multiple swaggers exist.
        return self.on_page_markdown(markdown, page, config, files)
