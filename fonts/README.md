## LibreOffice fonts

This directory contains fonts used by the LibreOffice main document.
Note that the fonts could have been included directly into the LibreOffice documents.
But that would have increased the size of the documents.
Also, when I tested this, LibreOffice crashed. Presumably it crashed because of the size and the
number of sub documents (over 1400) that are included from the main document.

So we chose to separate the fonts from the documents.

## Usage

In order for LibreOffice to recognize and use these fonts, you can use either of the following
approaches:

- Run LibreOffice from the docker container. This will automatically mount the fonts into the
docker container, or

- Install the fonts on your computer (and run LibreOffice from your computer).

## Installation of fonts

After installing the fonts, you should restart LibreOffice for it to recognize the new fonts.

### Linux

- Copy the fonts in this directory to `~/.local/share/fonts/`

### macOS

- Open the FontBook app. Drag the files in this directory into the app window. You may need to restart
your computer for the fonts to be recognized.

### Windows

- The fonts should be copied to `C:\Windows\Fonts`. However, when I tested this it seems it is not
possible to copy all fonts at once. You need to double-click on each font to open the font preview window
and from there click the "Install" button.



