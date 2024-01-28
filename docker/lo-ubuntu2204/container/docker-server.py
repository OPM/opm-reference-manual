import logging
import os
#import subprocess
from pathlib import Path

from flask import Flask, request

import uno

from unohelper import systemPathToFileUrl, absolutize
from com.sun.star.beans import PropertyValue

app = Flask(__name__)

def update_indexes(doc):
    """
    Update all indexes in the given document.
    """
    try:
        indexes = doc.getDocumentIndexes()
        for i in range(0, indexes.getCount()):
            index = indexes.getByIndex(i)
            index.update()
        logging.info("Indexes updated successfully.")
    except Exception as e:
        logging.error("Error updating indexes and tables: " + str(e))

def open_document_with_libreoffice(doc_path: str):
    # Connect to the running instance of LibreOffice
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    # Load the document
    cwd = systemPathToFileUrl( os.getcwd() )
    path_ = "parts" / Path(doc_path)
    file_url = absolutize( cwd, systemPathToFileUrl(str(path_)) )

    load_props = []
    #load_props.append(PropertyValue(Name="Hidden", Value=True))  # Open document hidden
    #load_props.append(PropertyValue(Name="UpdateDocMode",
    #            Value=uno.getConstantByName("com.sun.star.document.UpdateDocMode.QUIET_UPDATE")))
    load_props = tuple(load_props)

    logging.info("Loading {}".format(file_url))
    doc = desktop.loadComponentFromURL(file_url, "_blank", 0, load_props)

    update_indexes(doc)

    # Save the document
    #doc.store()
    #doc.dispose()
    logging.info("Done")


@app.route('/open-document', methods=['POST'])
def open_document():
    # Extract the document path from the request
    doc_path = request.json.get('path')

    # Replace this with the command to open the document using LibreOffice
    open_document_with_libreoffice(doc_path)
    return "Document opened", 200

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # ASSUME: libreoffice deamon process has already been started and listening
    #   on port 2002 at localhost :
    #
    #    libreoffice --accept="socket,host=localhost,port=2002;urp;" --pidfile=lo_pid.txt
    #
    app.run(debug=True, host='0.0.0.0', port=8080)

