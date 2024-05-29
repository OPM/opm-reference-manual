

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
$ fodt-add-keyword --maindir=../../parts --keyword=HELLO --section=4.3 --title="Hello World" --status=green
```
will add a keyword `HELLO` to section 4.3. It will be assumed that the keywords are sorted
alphabetically in the subsection which is used to determine the position of the keyword
within the section. In addition, an entry for the keyword is added to alphabetical listing
of keywords in Appendix A with the
status color green specified by the `--status=green` option. The `--title="Hello world"`
argument sets the short title for the keyword in both section 4.3 and in the Appendix A.

For the above example, adding the keyword involves updating the sub document `parts/chapters/4.fodt`
to include the new file `parts/chapters/subsections/4.3/HELLO.fodt`.
The generated file `HELLO.fodt` is created from a template such that it initially contains just
the heading with the keyword name.

Note: In the rare case you want to add the same keyword name to different sections, you can avoid adding the keyword twice to Appendix A by giving option `--no-appendix`.

## Changing the status of a keyword in Appendix A

To change the status of a keyword in the status column in the alphabetical listing
of keywords in Appendix A, run for example:

```
$ fodt-set-keyword-status --keyword=CSKIN --color=green --opm-flow
```

this will change the color from orange to green and add the text "OPM Flow" to indicate
that the keyword is specific to OPM flow. If the keyword is not specific to OPM flow,
just omit the `--opm-flow` flag.

## Submitting a PR for a change to a `.fodt` file

If you modify one of the `.fodt` files in the `parts` folder using LibreOffice and then
save it, LibreOffice will usually restructure the internally used XML tag attribute style
names. These changes are of no importance for the real change you made to the document
but will show up in a Git diff if you submit a pull request for the change and will
make the review of your change more difficult for the reviewers (since they have to
search through the whole diff for the actual change you made).

To improve on this situation, there is a script `fodt-split-commit` that can be used
to split a commit into two parts. The first part commit contains the style changes that
is usually not important for the reviewer, and the second part commit contains the
real changes. The reviewer can then focus on reviewing the second part.

The requirement for using the script is that the last commit contain changes to a single
`.fodt` file. The commit message of the last commit will be used as a prefix for the commit
messages of the two new commits (that replaces the current commit) with style
and content changes. See the documentation in the source code [split_git_commit.py](src/fodt/split_git_commit.py) for more details.


## Exporting the manual as PDF

Open `main.fodt`. Select from the menu item `Tools` → `Update` → `Indexes and Tables`.
You may have to wait some minutes for the update to complete.

You can now export the manual to PDF. From the `File` menu, select "Export As" → "Export as PDF…",
and click the "Export" button in the dialog, then choose a filename for the PDF file.

## If the main document is modified

As noted above, the main document `main.fodt` would generally not be edited (or resaved). It is
mainly used for exporting the manual to PDF format. If it needs to be modified, data that was
extracted from it may need to be re-extracted. From the ``scripts`` folder we can run the following commands
to re-extract (update) metadata:

```
$ fodt-extract-metadata --maindir=../../parts --filename=/tmp/Manual.fodt
$ fodt-extract-document-attrs --maindir=../../parts --filename=/tmp/Manual.fodt
$ fodt-extract-style-info --maindir=../../parts
```

Further, depending on the nature of the modification, all sub documents may also need to be updated.

## Previous work

See [Splitting](docs/Splitting-The-Manual.md) for the original work on splitting the manual into
sub documents.

