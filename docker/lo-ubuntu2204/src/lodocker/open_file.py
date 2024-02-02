import json
import logging
import requests
import os
from pathlib import Path

import click

def send_open_document_request(document_path: str):
    """Send a request to the LibreOffice server to open a document.
    :param document_path: The path to the document to open.
    """
    #path = Path(document_path)
    port = int(os.getenv('FLASK_PORT', 8080))
    url = f"http://localhost:{port}/open-document"
    headers = {"Content-Type": "application/json"}
    payload = {"path": document_path}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print(f"Document {document_path} opened successfully.")
    else:
        print(f"Failed to open document {document_path}. Status code: {response.status_code}")

@click.command()
@click.argument("document_path")
def open_file(document_path: str):
    logging.basicConfig(level=logging.INFO)
    send_open_document_request(document_path)

if __name__ == "__main__":
    open_file()
