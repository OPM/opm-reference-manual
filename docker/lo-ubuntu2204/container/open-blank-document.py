
import logging
import os
import uno

try:
    # Connect to the running instance of LibreOffice
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    port = int(os.getenv('LIBREOFFICE_PORT', 2002))
    ctx = resolver.resolve(f"uno:socket,host=localhost,port={port};urp;StarOffice.ComponentContext")
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    # Open a blank document
    document = desktop.loadComponentFromURL("private:factory/swriter", "_blank", 0, ())
except Exception as e:
    logging.error(f"Error in opening blank document: {e}")
