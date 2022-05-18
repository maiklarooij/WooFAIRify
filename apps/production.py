import re
import pdfplumber

def create_metadata(form_data, files):
    """
    Based on data from a form (attributes and file objects), creates a dict with all attributes.

    Arguments:
    - form_data: a multidict containing the parsed HTML form data
    - files: a multidict containing the uploaded files from the HTML form
    """
    # Split publication and document data
    publication_dict = {k: v for k, v in form_data.to_dict().items() if v and not re.match(r'^doc[0-9]{1}.', k)}
    document_dict = {k: v for k, v in form_data.to_dict().items() if v and re.match(r'^doc[0-9]{1}.', k)}
    files_dict =  {k: v for k, v in files.to_dict().items()}

    # Convert adjourned into a bool
    try:
        adjourned = True if publication_dict['adjourned'] == 'Ja' else False
        publication_dict['adjourned'] = adjourned
    except:
        pass

    # Extract for each document its attributes
    prefix_set = set([name.split('.')[0] for name in document_dict])
    documents = []
    for number, document_prefix in enumerate(prefix_set):
        document_attributes = {k.replace(document_prefix+'.', ''): v for k, v in document_dict.items() if k.startswith(document_prefix)}

        # Exceptional cases where identifier is not specified, prevent errors
        # Note: such an input will not pass validation
        if 'identifier' in publication_dict:
            document_attributes['identifier'] = f"{publication_dict['identifier']}-{number+1}"
        else: 
            document_attributes['identifier'] = number+1

        # Add grounds of refusal
        try:
            refusal_grounds = document_attributes['groundsOfRefusal'].split(",")
            document_attributes['groundsOfRefusal'] = refusal_grounds
        except:
            pass
        
        # Enrich document based on file
        document_attributes = enrich_document(files_dict[f"{document_prefix}.file"], document_attributes)
        documents.append(document_attributes)

    publication_dict['documents'] = documents
    publication_dict['numberDocuments'] = len(documents)

    return publication_dict

def enrich_document(document_object, document_attributes):
    """
    Based on the file object of a document, enrich a dict with attributes with metadata.
    Adds a mimeType, fileName and numberPages.

    Arguments:
    - document_object: a file stored as FileStorage object
    - document_attributes: the document object dict with document attributes
    """

    document_attributes['mimeType'] = document_object.mimetype
    document_attributes['fileName'] = document_object.filename
    document_attributes['fileExtension'] = document_object.filename.split('.')[-1]

    # pdfplumber only works with pdf files
    if document_object.mimetype == 'application/pdf':

        with pdfplumber.open(document_object) as pdf:
            document_attributes['numberPages'] = len(pdf.pages)

            # Try to find the number of characters, textpages and words
            chars = 0
            textpages = 0
            words = 0
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    chars += len(page_text)
                    textpages += 1
                    words += len(clean_split(page_text))

        document_attributes['numberCharacters'] = chars
        document_attributes['numberWords'] = words
        document_attributes['numberTextPages'] = textpages

    return document_attributes

def clean_split(text):
    """
    Splits and cleans a string of text.

    Arguments:
    - text: a text string
    """
    splitted = re.split('\W+', text)
    cleaned = [word.lower() for word in splitted if word]
     
    return cleaned