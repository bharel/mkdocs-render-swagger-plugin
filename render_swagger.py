import mkdocs.plugins
from pathlib import Path
from mkdocs.structure.files import File
import string
import re
from xml.sax.saxutils import escape

USAGE_MSG = ("Usage: '!!swagger <filename>!!'. "
             "File must exist locally and be placed next to the .md that contains "
             "the swagger statement.")

TEMPLATE = string.Template("""

<link type="text/css" rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css">
<div id="swagger-ui">
</div>
<script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js" charset="UTF-8"></script>
<script>
    const ui = SwaggerUIBundle({
    url: '$path',
    dom_id: '#swagger-ui',
    })
</script>

""")

ERROR_TEMPLATE = string.Template("!! SWAGGER ERROR: $error !!")

# Used for JS. Runs locally on end-user. RFI / LFI not possible, no security risk.
# Restrict to local file.
TOKEN = re.compile(r"!!swagger(?: (?P<path>[^\\/\s><&:]+))?!!")

class SwaggerPlugin(mkdocs.plugins.BasePlugin):
    def on_page_markdown(self, markdown, page, config, files):

        match = TOKEN.search(markdown)

        if match is None:
            return markdown

        pre_token = markdown[:match.start()]
        post_token = markdown[match.end():]

        def _error(message):
            return (pre_token + escape(ERROR_TEMPLATE.substitute(error=message)) +
                    post_token)

        path = match.group("path")

        if path is None:
            return _error(USAGE_MSG)

        try:
            api_file = Path(page.file.abs_src_path).with_name(path)
        except ValueError as exc:
            return _error(f"Invalid path. {exc.args[0]}")

        if not api_file.exists():
            return _error(f"File {path} not found.")

        src_dir = api_file.parent
        dest_dir = Path(page.file.abs_dest_path).parent

        new_file = File(api_file.name, src_dir, dest_dir, False)
        files.append(new_file)
        url = Path(new_file.abs_dest_path).name

        markdown = pre_token + TEMPLATE.substitute(path=url) + post_token

        # If multiple swaggers exist.
        return self.on_page_markdown(markdown, page, config, files)
