## Splitting the OPM flow manual file into sub files

The OPM flow manual is written in OpenDocument format. The file type is `.fodt`, also known as
[flat OpenDocument XML file](https://en.wikipedia.org/wiki/OpenDocument).
See [FODT-structure.md](docs/FODT-structure.md) for more information about the structure of
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

See [Converting-to-other-fileformats.md](docs/Converting-to-other-fileformats.md) for status on this work.

### Splitting the FODT into sub files

See [Splitting-Strategies.md](docs/Splitting-Strategies.md) for status on this work.

## Installation of the python scripts
- Requires python3 >= 3.10

### Using poetry
For development it is recommended to use poetry:

- Install [poetry](https://python-poetry.org/docs/)
- Then run:
```
$ poetry install
$ poetry shell
```

### Installation into virtual environment
If you do not plan to change the code, you can do a regular installation into a VENV:

```
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install .
```

## Splitting the manual

Run the command:

```
$ fodt-split-all --maindir=out --filename=../OPM_Flow_Reference_Manual.fodt
```

This will create a new main document in directory `out/main.fodt` and sub documents for each chapter
in directory `out/chapters`.

Then it will split sections 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, and 12.3 into subsections
in directory `out/chapters/subsections`. Each subsection document will be named after its keyword
name, for example `out/chapters/subsections/10.3/SALT.fodt`.

## Editing sub documents

After splitting, the new main document `main.fodt` should not be edited (or resaved). It will
only be used for exporting the manual to PDF format. Rather, edit the generated sub documents.

## Adding a keyword

After having split the main document into subsections, you can create a new subsection document by
using the `fodt-add-keyword` command, for example
```
$ fodt-add-keyword --maindir=../parts --keyword=HELLO --section=4.3
```
will add a keyword `HELLO` to section 4.3. It will be assumed that the keywords are sorted alphabetically
in the subsection which is used to determine the position of the keyword within the section.

For the above example, adding the keyword involves updating the sub document `parts/chapters/4.fodt`
to include the new file `parts/chapters/subsections/4.3/HELLO.fodt`.
The generated file `HELLO.fodt` is created from a template such that it initially contains just
the heading with the keyword name.

## Exporting the manual as PDF

Open `main.fodt`. Scroll down to the table of contents and right-click on an entry (e.g. Chapter 1).
Select "Update Index" from the popup menu. This will correct the numbering in the table of contents.
You may have to wait a minute for the update to complete.

You can now export the manual to PDF. From the `File` menu, select "Export As" → "Export as PDF…",
and click the "Export" button in the dialog, then choose a filename for the PDF file.

## If the main document is modified

As noted above, the main document `main.fodt` would generally not be edited (or resaved). It is
mainly used for exporting the manual to PDF format. If it needs to be modified, data that was
extracted from it may need to be re-extracted. From the ``scripts`` folder we can run the following commands
to re-extract (update) metadata:

```
$ fodt-extract-metadata --maindir=../parts --filename=../OPM_Flow_Reference_Manual.fodt
$ fodt-extract-document-attrs --maindir=../parts --filename=../OPM_Flow_Reference_Manual.fodt
$ fodt-extract-style-info --maindir=../parts
```

Further, depending on the nature of the modification, all sub documents may also need to be updated.

