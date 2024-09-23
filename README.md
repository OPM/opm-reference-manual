# The OPM Flow Reference Manual

This repository contains the uncompressed LibreOffice XML files (ending in
`.fodt`) used for creating the OPM Flow Reference Manual.

## Structure of the documents.

To make the rather large manual feasible to edit on most systems, the document
is organized as a master document (`parts/main.fodt`) which contains links to
many other LibreOffice documents that contain the individual parts.

Each chapter is in its own document (e.g. `parts/chapters/1.fodt` for Chapter 1). The same holds for the appendices (e.g
`parts/appendices/A.fodt` for Appendix A).

Many of the chapter files themselves contain links to external documents. These
represent sections (e.g. `parts/chapters/sections/4/3.fodt` for section
4.3 that is linked to from `parts/chapters/4.fodt`).

The special subsections (4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, and 12.3)
contain all the descriptions of the keywords supported or not supported by
OPM Flow. Each keyword is described in its
own LibreOffice file and referenced as an external link in the chapter file.
An example of a keyword file is `parts/chapters/subsections/4.3/COLUMNS.fodt`.

## Editing the manual/Submitting Pull Requests

Note that any document containing links to external documents should never be
edited directly. If such a document would be saved then LibreOffice would
remove all the links to the external documents and instead embed those documents
into the document that is edited. This would break the above described
structure.

Make sure to disable document comparison mode in LibreOffice. Since we already
use version control with Git, it would make editing the documents more difficult
if LibreOffice also saved version information into the files. The option can be
disabled in LibreOffice by choosing the menu item Tools → Options → LibreOffice Writer → Comparison and then uncheck the box "Store it when changing the document", see [screenshot](assets/option-doc-comparison-store-it-when-changing-the-document.png).

Please note that this setting might influence your whole LibreOffice experience as it is used whenever you open LibreOffice. If you do not want that then you will need to set it back after editing the manual.

For simple changes (e.g. typos) the XML code of the .fodt file can be edited directly in a text editor. This has the advantage that it introduces less changes than if the file had been edited with LibreOffice.

## Reviewing Pull Requests

A list of the files changed by a PR can be viewed on GitHub by clicking the `Files changed` tab on the PR. The changed .fodt files can be downloaded by clicking `View file` from the `...` menu and then clicking the `Download raw file` icon. The .fodt files can then be opened and reviewed in LibreOffice.

When a file is opened LibreOffice may ask `Would you like to change the document, and update all links to get the most recent data?`. It is recommended that you click No for downloaded files. This will allow you to view the file without any of the externally linked documents included.

GitHub attempts to show the changes to the XML code on the `Files changed` tab but where the files have been edited with LibreOffice the changes are often too large to display. 

## Exporting the manual as PDF

Open `main.fodt`. Select from the menu item `Tools` → `Update` → `Indexes and Tables`.
You may have to wait some minutes for the update to complete.

You can now export the manual to PDF. From the `File` menu, select "Export As" → "Export as PDF…",
and click the "Export" button in the dialog, then choose a filename for the PDF file.

## Further information

For further information please see the following READMEs:

- [fonts/README.md](fonts/README.md) for information about how to display the
  documents correctly with the correct fonts (e.g. using docker)
- [scripts/python/README.md](scripts/python/README.md) for information about the scripts
  used for splitting the original document.
