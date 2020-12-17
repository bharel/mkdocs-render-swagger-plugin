# mkdocs-render-swagger-plugin
This is the [Mkdocs](https://mkdocs.org) plugin for rendering swagger &amp; openapi schemas using Swagger UI. It is written in Python.

## Usage
Add the following lines to your mkdocs.yml:

    plugins:
      - render_swagger
    
Enter `!!swagger <filename>!!` at the appropriate location inside a markdown file.

## Running Locally

You can install this package locally using `pip` and the `--editable` flag used for making developing Python packages.

```bash
pip install --editable .
```

You'll then have the `render-swagger` package available to use in Mkdocs and `pip` will point the dependency to this folder.

## MkDocs plugins and Swagger api

The Render Swagger MkDocs plugin comes with a set of extensions and plugins that mkdocs and Swagger UI supports.
You can find a list of all the MkDocks plugins and Swagger UI that are included in the Render Swagger plugin on the official website of [MkDocks](https://www.mkdocs.org/user-guide/plugins/) and [SwaggerUI](https://github.com/swagger-api/swagger-ui/blob/master/docs/customization/plugin-api.md)

</br>
<small>
Disclaimer: This plugin is unofficial, and is not sponsored, owned or endorsed by mkdocs, swagger, or any other 3rd party.</br>
Credits to @aviramha for starting this project.
</small>
