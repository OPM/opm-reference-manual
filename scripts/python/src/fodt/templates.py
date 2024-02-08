class Templates:
    class AppendixA:
        class Styles:
            table_row_template = (
""" <style:style style:name="AppendixA_TableRow" style:family="table-row">
  <style:table-row-properties fo:background-color="transparent" fo:keep-together="always">
   <style:background-image></style:background-image>
  </style:table-row-properties>
</style:style>""")
            table_cell_template = (
""" <style:style style:name="AppendixA_TableCell" style:family="table-cell">
  <style:table-cell-properties style:vertical-align="middle" fo:background-color="transparent" fo:padding="0.102cm" fo:border-left="0.05pt solid #000000" fo:border-right="none" fo:border-top="none" fo:border-bottom="0.05pt solid #000000">
   <style:background-image/>
  </style:table-cell-properties>
 </style:style>""")
            table_cell_orange_template = (
""" <style:style style:name="AppendixA_TableCell_Orange" style:family="table-cell">
  <style:table-cell-properties fo:background-color="#ff950e" fo:padding="0.102cm" fo:border-left="0.05pt solid #000000" fo:border-right="0.05pt solid #000000" fo:border-top="none" fo:border-bottom="0.05pt solid #000000">
   <style:background-image/>
  </style:table-cell-properties>
 </style:style>""")
            table_cell_green_template = (
""" <style:style style:name="AppendixA_TableCell_Green" style:family="table-cell">
  <style:table-cell-properties fo:background-color="#579d1c" fo:padding="0.102cm" fo:border-left="0.05pt solid #000000" fo:border-right="0.05pt solid #000000" fo:border-top="none" fo:border-bottom="0.05pt solid #000000">
   <style:background-image/>
  </style:table-cell-properties>
 </style:style>""")
        class Content:
            table_row_template = (
"""     <table:table-row table:style-name="AppendixA_TableRow">\n"""
"""      <table:table-cell table:style-name="AppendixA_TableCell" """
                 """table:number-columns-spanned="7" office:value-type="string">\n"""
"""       <text:p text:style-name="_40_Table_20_Contents">"""
                 """<text:a xlink:type="simple" xlink:href="#0.0.0.###KEYWORD_NAME###" """
                 """text:style-name="Internet_20_link" """
                 """text:visited-style-name="Visited_20_Internet_20_Link">"""
                 """<text:bookmark-ref text:reference-format="text" """
                 """text:ref-name="REF_HEADING_KEYWORD_###KEYWORD_NAME###">"""
                 """###KEYWORD_NAME### – ###KEYWORD_DESCRIPTION###"""
                 """</text:bookmark-ref></text:a></text:p>\n"""
"""      </table:table-cell>
      <table:covered-table-cell></table:covered-table-cell>
      <table:covered-table-cell></table:covered-table-cell>
      <table:covered-table-cell></table:covered-table-cell>
      <table:covered-table-cell></table:covered-table-cell>
      <table:covered-table-cell></table:covered-table-cell>
      <table:covered-table-cell></table:covered-table-cell>
      <table:table-cell table:style-name="AppendixA_TableCell_###COLOR###" """
                                     """office:value-type="string">\n"""
"""       <text:p text:style-name="_40_Table_20_Contents"></text:p>
      </table:table-cell>
     </table:table-row>""")


