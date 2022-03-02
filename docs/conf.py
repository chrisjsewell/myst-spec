"""Configuration for sphinx documentation."""
import json
from textwrap import dedent

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
import yaml

from myst_spec_py import mdit_to_mdast

extensions = ["myst_parser", "sphinx_design", "sphinx_copybutton"]

myst_title_to_header = True
html_theme = "furo"
html_title = "MyST Specification"


class SpecExample(SphinxDirective):
    """Directive for including an example of a spec."""

    has_content = True

    def run(self) -> None:
        """Run the directive."""
        # keep track of the example number within the document
        self.env.metadata[self.env.docname].setdefault("spec_example_num", 0)
        self.env.metadata[self.env.docname]["spec_example_num"] += 1
        spec_example_num = self.env.metadata[self.env.docname]["spec_example_num"]
        # the markdown and HTML should be separated by a line containing a single `.`
        markdown = "\n".join(self.content[: self.content.index(".")])
        html = "\n".join(self.content[self.content.index(".") + 1 :])
        ast = mdit_to_mdast.parse(markdown)
        # convert to a standard dict, so it can then be converted to YAML
        ast_yaml = yaml.safe_dump(
            json.loads(json.dumps(ast, sort_keys=False)), sort_keys=False
        )
        # create the tabs content
        tabs_content = f"""
```{{rubric}} Example {spec_example_num}:
```
``````````{{tab-set}}

`````````{{tab-item}} Markdown
````````markdown
{markdown}
````````
`````````

`````````{{tab-item}} MDAST
````````yaml
{ast_yaml}
````````
`````````

`````````{{tab-item}} HTML
````````html
{html}
````````
`````````

``````````
        """
        node = nodes.Element()  # anonymous container for parsing
        self.state.nested_parse(tabs_content.splitlines(), self.content_offset, node)
        return node.children


def setup(app: Sphinx) -> None:
    """Set up the Sphinx application."""
    app.add_directive("spec-example", SpecExample)
