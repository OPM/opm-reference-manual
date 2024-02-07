# The OPM-flow reference manual

This repository contains the uncompressed LibreOffice XML files (ending in
.fdot) used for creating the reference manual of flow

## Structure of the documents.

To make the rather large manual feasible to edit on most systems, the document
is organized as a master document (part/main.fodt) which contains links to many
other LibreOffice documents that contain the individual parts.

Each chapter is in its own document (e.g. parts/chapters/1.fdot for the first
chapter). The same holds for the chapters of the appendices (e.g
parts/appendices/A.fdot for Appendix A).

Many of the chapter files contain themselves links to external documents. Those
are representing sections (e.g. parts/chapters/sections/4/3.fodt  for section
4.3 that is linked to from parts/chapters/4).

The special subsections (4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, and 12.3)
contain all the descriptions of the keywords supported or not supported by
flow. Each keyword is described in its
own LibreOffice file and referenced as an external link in the subsection file.
An example of such a file is parts/chapters/subsections/4.3/COLUMNS.fodt.

## Editing the manual

Note that any document containing link to external documents should never be
edited directly. If such a document would be saved then LibreOffice would
remove all the links to the external documents and instead embed those documents
into the document that is edited. This would break the above described
structure.

## Exporting the manual as PDF

Open `main.fodt`. Scroll down to the table of contents and right-click on an entry (e.g. Chapter 1).
Select "Update Index" from the popup menu. This will correct the numbering in the table of contents.
You may have to wait a minute for the update to complete.

You can now export the manual to PDF. From the `File` menu, select "Export As" → "Export as PDF…",
and click the "Export" button in the dialog, then choose a filename for the PDF file.

## Further information

For further information please see the following READMEs
- [fonts/README.md](fonts/README.md) for information about how to display the
  documents correctly with the correct fonts (e.g. using docker)
- [scripts/README.md](scripts/README.md) for information about the scripts
  used for splitting the original document.
