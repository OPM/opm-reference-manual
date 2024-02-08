## Splitting the OPM flow manual file into sub files

The OPM flow manual is written in OpenDocument format. The file type is `.fodt`, also known as
[flat OpenDocument XML file](https://en.wikipedia.org/wiki/OpenDocument).
See [FODT-structure.md](FODT-structure.md) for more information about the structure of
this file.
The published manual
is obtained by exporting the FODT file to PDF from within LibreOffice.

The current size of the FODT file is around 75 Mb or around 920,000 lines of XML.
If the file is opened in LibreOffice and rendered as the actual open document, it has around 3000 pages.

### Why do we want to split up the file?

The size of the file has become too large to be handled efficiently by LibreOffice.
It takes almost a minute to load the file on my laptop, and when loaded it will
often freeze up when I try to edit or copy some part or scroll around in the document.

## Ideas/plans for splitting the document

### Converting to other file formats

An idea could be to convert the manual into other (simpler) formats like
[restructured text](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html), or HTML.
Then, split into sub files of this type. Such documentation could be hosted online as a website,
in contrast to the current single document PDF file. If this is also hosted on GitHub, it could make
it easier for different people to contribute to the documentation by submitting pull requests.

See [Converting-to-other-fileformats.md](Converting-to-other-fileformats.md) for status on this work.

### Splitting the FODT into sub files

See [Splitting-Strategies.md](Splitting-Strategies.md) for status on this work.

## Splitting the manual

- First install the python modules, see the [README](../README.md) for more information on installation.

- Run the command:

```
$ fodt-split-all --maindir=out --filename=/tmp/Manual.fodt
```

This will create a new main document in directory `out/main.fodt` and sub documents for each chapter
in directory `out/chapters`.

Then it will split sections 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, and 12.3 into subsections
in directory `out/chapters/subsections`. Each subsection document will be named after its keyword
name, for example `out/chapters/subsections/10.3/SALT.fodt`.
