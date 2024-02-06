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

def open_document_with_libreoffice(doc_path: str, do_update_indexes=True):
    # Connect to the running instance of LibreOffice
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    port = int(os.getenv('LIBREOFFICE_PORT', 2002))
    ctx = resolver.resolve(f"uno:socket,host=localhost,port={port};urp;StarOffice.ComponentContext")
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

    if do_update_indexes:
        update_indexes(doc)

    # Save the document
    # The user can save the document from the menu for now.
    # If we want to automate the saving process we can do that by running libreoffice
    # in headless mode using doc.store() as shown below
    #doc.store()
    #doc.dispose()
    logging.info("Done")


@app.route('/open-document-and-update', methods=['POST'])
def open_document_and_update():
    # Extract the document path from the request
    doc_path = request.json.get('path')

    # Replace this with the command to open the document using LibreOffice
    open_document_with_libreoffice(doc_path, do_update_indexes=True)
    return "Document opened", 200

@app.route('/open-document', methods=['POST'])
def open_document():
    # Extract the document path from the request
    doc_path = request.json.get('path')

    # Replace this with the command to open the document using LibreOffice
    open_document_with_libreoffice(doc_path, do_update_indexes=False)
    return "Document opened", 200


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # ASSUME: libreoffice deamon process has already been started and listening
    #   on port 2002 at localhost :
    #
    #    libreoffice --accept="socket,host=localhost,port=2002;urp;" --pidfile=lo_pid.txt
    #
    port = int(os.getenv('FLASK_PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)

