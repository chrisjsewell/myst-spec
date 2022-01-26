# MyST Specification (IN-DEVELOPMENT)

A specification for a CommonMark compliant AST format

## Introduction

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

Inspiration taken from:

- Markdown-it tokens
- Docutils doctree's
- Pandoc JSON AST
- https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocuments

## Notes

- Markdown-it is not actually the ideal reference implementation, since it does not capture source columns.
- docutils records the source for every node, since it may be different to the parent document, if using the `include` directive.


[commonmark-spec]: https://github.com/commonmark/commonmark-spec/
[lsp]: https://microsoft.github.io/language-server-protocol/
