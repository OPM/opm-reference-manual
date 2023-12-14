

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

## Editing sub documents

The main document `parts/main.fodt` should not be edited (or resaved). It will
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

## Changing the status of a keyword in Appendix A

To change the status color of a keyword in the status column in the alphabetic listing of keywords
in Appendix A, run for example:

```
$ fodt-set-ketword-status --keyword=CSKIN --color=green
```

this will change the color from orange to green.

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

## Previous work

See [Splitting](docs/Splitting-The-Manual.md) for the original work on splitting the manual into
sub documents.

