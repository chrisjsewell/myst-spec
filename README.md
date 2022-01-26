# MyST Specification (IN-DEVELOPMENT)

A CommonMark compliant AST format for the MyST specification.

This is some initial work on a specification for the MyST syntax.

The package currently contains functions to:

1. Convert CommonMark to [mdast](https://github.com/syntax-tree/mdast), via parsing with [Markdown-it](https://github.com/markdown-it/markdown-it)
2. Convert the mdast to CommonMark compliant HTML (tested against <https://spec.commonmark.org/0.30/spec.json>)

```console
$ pip install .
$ myst-spec --help
usage: myst-spec [-h] COMMAND ...

MyST Specification tools.

optional arguments:
  -h, --help  show this help message and exit

Commands:
    to-mdast  Convert CommonMark to MDAST JSON.
    to-html   Convert CommonMark to HTML.

```

This can then be extended, to include the MyST syntax nodes.

## The CommonMark Specification

The creation of [commonmark-spec] represented a great step forward in Markdown standardisation.
However, the current specification only specifies the expected HTML output, which conflates two aspects of markup language processing:

- The reading of the source input
- The writing of the output format

There are other aspects of Markdown processing that would benefit from such a specification, such as:

- Output to other formats than HTML
- Syntax highlighting of the source text
- [Language Server Protocol][lsp] integration

This would promote interoperability between different implementations for reading and processing of Markdown.

Note, there is an open issue ([#274](https://github.com/commonmark/commonmark-spec/issues/274)), suggesting an XML specification,
but this discussion has not been re-visited since 2017.

## Design decisions

- The format should be language agnostic.
  - A program written in any programming language should be able to generate the AST, then offload to a different language for processing.
- The format should be extensible.
  - The format should allow for new syntax types to be added, and not hard-code to only the CommonMark types.
  - Not all processor may be able to handle extended syntax types, but they should be able to "fail gracefully"
  - An example of this would be to allow for the [GitHub Flavored Markdown extensions](https://github.github.com/gfm/)
- The AST format should be lossless.
  - The AST should be able to be converted back to the source text, without loss of syntax information.
  - Note, this does not mean that round-trip conversion should be "byte equivalent", just that it will produce again the same AST.
  - Line/column information, for example, would not be preserved.
- The format should allow incremental parsing.
  - This would allow for sub-parsing of modified document, without having to re-parse the entire document.

Inspiration also taken from:

- Markdown-it tokens
- Docutils doctree's
- Pandoc JSON AST
- https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocuments
- https://github.com/agoose77/jupyterlab-markup/issues/12

## Markdown-It to MDAST

[Markdown-it-py](https://github.com/ExecutableBookProject/markdown-it-py) is used as the parser here,
since it is what we currently use for [MyST-Parser](https://github.com/executablebooks/MyST-Parser).
It is the best Python Markdown parser I know of:

- It is pure-python
- It is fast
- It is CommonMark compliant
- It captures source line number information
- It is easy to extend by plugins

However, it is not actually the ideal reference implementation, since it does not capture source column position information.
Also, the conversion here is not currently supported by the Markdown-IT JS implementation,
since we utilise the `store_labels` and `inline_definitions` options, which are only implemented in markdown-it-py.

## Notes

- docutils records the source for every node, since it may be different to the parent document, if using the `include` directive.


[commonmark-spec]: https://github.com/commonmark/commonmark-spec/
[lsp]: https://microsoft.github.io/language-server-protocol/
