import setuptools

# Read the contents of the README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="mkdocs-render-swagger-plugin",
    version="0.0.1",
    author="Bar Harel",
    python_requires='>=3.6',
    author_email="bzvi7919@gmail.com",
    description="MKDocs plugin for rendering swagger & openapi files.",
    url="https://github.com/bharel/mkdocs-render-swagger-plugin",
    py_modules=["render_swagger"],
    install_requires=["mkdocs"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'mkdocs.plugins': [
            'render_swagger = render_swagger:SwaggerPlugin',
        ]
    },
    long_description=long_description,
    long_description_content_type='text/markdown'
)
