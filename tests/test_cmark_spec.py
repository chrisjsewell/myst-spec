import json
from pathlib import Path

import pytest

from myst_spec_py.mdast_to_html import render
from myst_spec_py.mdit_to_mdast import parse

spec_path = Path(__file__).parent.joinpath("static", "cmark_spec_0.30.json")


@pytest.mark.parametrize(
    "test_data",
    json.loads(spec_path.read_text("utf8")),
    ids=lambda x: f'example-{x["example"]}',
)
def test_cmark_spec(test_data):
    """Test the cmark spec."""
    markdown = test_data["markdown"]
    output = render(parse(markdown))
    try:
        assert output == test_data["html"]
    except AssertionError:
        # print(markdown)
        # print(parse(markdown))
        print(output.replace("\n", "\\n"))
        print("***")
        print(test_data["html"].replace("\n", "\\n"))
        raise
