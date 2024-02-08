## Use Libreoffice builtin conversion engines to convert to other file formats

Libreoffice has builtin conversions to various file formats:
docx, xhtml, html, and rich text format, among others.

### XHTML

I tried to convert to XHTML, but it seems to get stuck. I killed the process after waiting for 15
minutes.

### HTML
Conversion to HTML did work. The genereated HTML had around 400,000 lines. In addition all figures
and tables was saved as separate png and gif files. A number of 502 gif files and 150 png files
was generated.

### RTF
Conversion to RTF seems also to work. The generated file had 3,950,000 lines and was around
500 Mb in size. This is over 5 times as large as the original FODT file.

## Splitting the document using the pandoc utility script

According to the [documentation](https://pandoc.org/) for PanDoc it should be possible to 
convert ODT files into other file formats that would be more easy to handle.

I first saved the FODT document as ODT from the Libreoffice save menu, then tried to convert
using pandoc. However, both conversion to markdown and html failed.
