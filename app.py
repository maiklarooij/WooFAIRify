from importlib.metadata import metadata
from flask import Flask , request, render_template, Response
from tempfile import mkdtemp

from apps.production import create_metadata
from apps.validation import validate_metadata
import json
from time import strftime, gmtime
import pandas as pd
import os

# Configure applicatioN
app = Flask(__name__)
app.config["SECRET_KEY"] = b'5\x95@j\xd7Z}\xd6\xfd\xafV\xfbU\xd6/\xf5'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

@app.route("/", methods=["GET"])
def start():
    """ Main page """

    # Render start template
    return render_template("index.html")

@app.route("/create_publication", methods=["GET"])
def create_publication():
    """ Main page """

    # Render start template
    return render_template("createjson.html")

@app.route("/create_json", methods=["POST"])
def create_json():
    """
    Retrieve form data, create and validate JSON
    """

    form_data = request.form
    files = request.files

    metadata_object = create_metadata(form_data, files)
    validation_result = validate_metadata(metadata_object)

    if validation_result == True:
        return generate_resultpage(metadata_object)
    else:
        return render_template('invalidpage.html', errors=validation_result, metadata_string=json.dumps(metadata_object, indent=4))

@app.route("/download_json", methods=["POST"])
def download_json():
    """ 
    Download JSON button is clicked, sending an HTTP response containing the file to the user for download.
    """
    metadata_string = request.form.get('metadatastring')

    timestamp = strftime("%Y%m%d-%H%M", gmtime())
    filename = f"export_{timestamp}.json"

    return Response(metadata_string, 
            mimetype='application/json',
            headers={'Content-Disposition':f'attachment;filename={filename}'})

@app.route("/upload_publication", methods=["GET", "POST"])
def upload_json(method='normal'):
    """ 
    Handles file uploads for validation
    """
    if request.method == 'GET':
        return render_template('uploadjson.html')
    else:
        if method == 'example':
            metadata_object = json.load(open('documentation/example publication/metadata/ZW8-data.json'))
        else:
            metadata_object = json.load(request.files['file'])
        validation_result = validate_metadata(metadata_object)

        if validation_result == True:
            return generate_resultpage(metadata_object)
        else:
            return render_template('invalidpage.html', errors=validation_result, metadata_string=json.dumps(metadata_object, indent=4))


@app.route("/exampleproduction", methods=["POST", "GET"])
def exampleproduction():
    """
    Shows an example to the user.
    """
    if request.method == "GET":
        return render_template('exampleproduction.html')

    return upload_json(method='example')

@app.route("/examplevalidation", methods=["POST", "GET"])
def examplevalidation():
    """
    Shows a validation example to the user.
    """
    if request.method == "GET":
        files = os.listdir('documentation/example publication/documenten')
        return render_template('examplevalidation.html', files=files)

    return upload_json(method='example')


def generate_resultpage(metadata_object):
    """
    Creates a result page with the validated data.
    """
    table_metadata = [{k: v for k, v in document.items() if 'bodyText' not in k} for document in metadata_object['documents']]
    doc_table = pd.DataFrame(table_metadata).to_html(border=0, classes="table table-striped")
    infobox = pd.DataFrame.from_dict(metadata_object, orient="index").drop('documents').to_html(border=0, classes="table table-striped", header=False)
    metadata_string = json.dumps(metadata_object, indent=4)

    return render_template('validpage.html', metadata=metadata_object, 
                                             table=doc_table, 
                                             metadata_string=metadata_string,
                                             infobox=infobox)