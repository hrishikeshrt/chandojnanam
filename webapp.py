#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 16:11:35 2019

@author: Hrishikesh Terdalkar
"""

import datetime

from flask import (
    Flask, request, render_template, flash,  # , url_for, redirect,
    send_from_directory
)
from flask_uploads import (
    UploadSet, IMAGES, TEXT, configure_uploads, patch_request_class
)

import pytesseract
from google_drive_ocr import GoogleOCRApplication
from indic_transliteration import sanscript

from chanda import Chanda
from settings import (
    APPLICATION_NAME, SECRET_KEY,
    TEMPLATE_PATH, STATIC_PATH,
    DATA_PATH, TMP_PATH, CLIENT_SECRET
)

###############################################################################

CHANDA = Chanda(DATA_PATH)

# --------------------------------------------------------------------------- #
# Upload Paths

PHOTOS_PATH = TMP_PATH / "photos"
TEXTS_PATH = TMP_PATH / "texts"

# Result Path
RESULTS_PATH = TMP_PATH / "results"

# Create Paths
TMP_PATH.mkdir(parents=True, exist_ok=True)
PHOTOS_PATH.mkdir(parents=True, exist_ok=True)
TEXTS_PATH.mkdir(parents=True, exist_ok=True)
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# OCR Instance

GoogleOCR = GoogleOCRApplication(
    client_secret=CLIENT_SECRET,
    temporary_upload=True
)

###############################################################################

webapp = Flask(APPLICATION_NAME,
               template_folder=TEMPLATE_PATH,
               static_folder=STATIC_PATH)
webapp.secret_key = SECRET_KEY
webapp.jinja_env.policies["json.dumps_kwargs"] = {
    'ensure_ascii': False,
    'sort_keys': False
}

webapp.config['UPLOADED_PHOTOS_DEST'] = str(PHOTOS_PATH)
webapp.config['UPLOADED_TEXTS_DEST'] = str(TEXTS_PATH)

photos = UploadSet('photos', IMAGES)
texts = UploadSet('texts', TEXT)

configure_uploads(webapp, (photos, texts,))
patch_request_class(webapp, 5 * 1024 * 1024)  # Limit: 5 megabytes

###############################################################################


@webapp.context_processor
def inject_global_constants():
    return {
        'now': datetime.datetime.utcnow(),
        'available_schemes': [
            ("", "Match Input"),
            ("devanagari", "Devanagari"),
            ("iast", "IAST"),
            ("itrans", "ITRANS"),
            ("hk", "Harvard-Kyoto"),
            ("wx", "WX"),
            ("slp1", "SLP1"),
            ("assamese", "Assamese"),
            ("bengali", "Bangla"),
            ("gujarati", "Gujarati"),
            ("kannada", "Kannada"),
            ("malayalam", "Malayalam"),
            ("oriya", "Oriya"),
            ("tamil", "Tamil"),
            ("telugu", "Telugu"),
        ],
        'text_modes': [
            ("verse", "Verse Mode"),
            ("line", "Line Mode")
        ]
    }


@webapp.template_filter('transliterate')
def transliterate_filter(text, scheme):
    if scheme is not None and scheme != sanscript.DEVANAGARI:
        return sanscript.transliterate(text, sanscript.DEVANAGARI, scheme)
    return text


###############################################################################


@webapp.route('/text', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_text():
    data = {}
    data['title'] = 'Identify from Text'
    data['text_mode'] = 'line'

    if request.method == 'POST':
        data['text'] = request.form['input_text']
        data['output_scheme'] = request.form.get('output_scheme', None)
        data['text_mode'] = request.form.get('text_mode', 'line')
        verse_mode = data['text_mode'] == "verse"

        webapp.logger.info(f"INPUT: {data['text']}")
        try:
            answer = CHANDA.identify_from_text(
                data['text'],
                verse=verse_mode,
                fuzzy=True,
                save_path=RESULTS_PATH
            )
            data['result'] = answer['result']
            data['result_path'] = answer['path']
            data['summary'] = CHANDA.summarize_results(data['result'])
            data['summary_pretty'] = CHANDA.format_summary(data['summary'])
        except Exception as e:
            flash(f"Something went wrong. ({e})")
            webapp.logger.exception(str(e))

    return render_template('text.html', data=data)


@webapp.route('/image', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_image():
    data = {}
    data['title'] = 'Identify from Image'
    data['engines'] = {
        'google': 'Google OCR',
        'tesseract': 'Tesseract OCR'
    }
    data['engine'] = 'tesseract'
    data['text_mode'] = 'line'

    if request.method == 'POST':
        data['text'] = request.form.get('input_text', '')
        data['output_scheme'] = request.form.get('output_scheme', None)
        data['text_mode'] = request.form.get('text_mode', 'line')
        verse_mode = data['text_mode'] == "verse"

        image_data = request.form.get('image_data')
        if image_data:
            data['image'] = image_data

        image_file = request.files.get('image_file')
        if image_file and image_file.filename:
            filename = photos.save(request.files['image_file'])
            filepath = PHOTOS_PATH / filename

            ocr_engine = request.form.get('ocr-engine', 'tesseract')
            output_path = filepath.with_suffix(f'.{ocr_engine}.txt')
            data['engine'] = ocr_engine

            import base64
            with open(filepath, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode("utf-8")

            data['image'] = image_base64

            if ocr_engine == 'google':
                status = GoogleOCR.perform_ocr(
                    filepath,
                    output_path=output_path
                )
                with open(output_path, "r", encoding="utf-8") as f:
                    data['text'] = f.read()
            if ocr_engine == 'tesseract':
                tesseract_config = '-l san+mar+hin+ben+tel+guj+tam+mal+kan'
                data['text'] = pytesseract.image_to_string(
                    str(filepath),
                    config=tesseract_config
                )
        else:
            if not data['text']:
                flash("Please select an image file.")

        webapp.logger.info(f"INPUT: {data['text']}")
        try:
            answer = CHANDA.identify_from_text(
                data['text'],
                verse=verse_mode,
                fuzzy=True,
                save_path=RESULTS_PATH,
                scheme=data['output_scheme']
            )
            data['result'] = answer['result']
            data['result_path'] = answer['path']
            data['summary'] = CHANDA.summarize_results(data['result'])
        except Exception as e:
            flash(f"Something went wrong. ({e})")
            webapp.logger.exception(str(e))

    return render_template('image_file.html', data=data)


@webapp.route('/file', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_file():
    data = {}
    data['title'] = 'Identify from Verse'
    data['text_mode'] = 'line'

    if request.method == 'POST':
        data['text'] = request.form.get('input_text', '')
        data['output_scheme'] = request.form.get('output_scheme', None)
        data['text_mode'] = request.form.get('text_mode', 'line')
        verse_mode = data['text_mode'] == "verse"

        if request.files['text_file'].filename:
            filename = texts.save(request.files['text_file'])
            filepath = TEXTS_PATH / filename

            with open(filepath, "r", encoding="utf-8") as f:
                data['text'] = f.read()

            webapp.logger.info(f"INPUT: {data['text']}")
            try:
                answer = CHANDA.identify_from_text(
                    data['text'],
                    verse=verse_mode,
                    fuzzy=True,
                    save_path=RESULTS_PATH,
                    scheme=data['output_scheme']
                )
                data['result'] = answer['result']
                data['result_path'] = answer['path']
                data['summary'] = CHANDA.summarize_results(data['result'])
            except Exception as e:
                flash(f"Something went wrong. ({e})")
                webapp.logger.exception(str(e))
        else:
            flash("Please select a text file to analyse.")

    return render_template('text_file.html', data=data)


@webapp.route('/download/<string:filename>')
def download_result(filename):
    return send_from_directory(RESULTS_PATH, filename)


@webapp.route('/', strict_slashes=False)
def home():
    data = {}
    data['title'] = 'About'
    return render_template('about.html', data=data)
    # return redirect(url_for('identify_line'), 307)


@webapp.route('/help', strict_slashes=False)
def show_help():
    data = {}
    data['title'] = 'Help'
    return render_template('help.html', data=data)


@webapp.route("/examples", strict_slashes=False)
def show_examples():
    data = {}
    data['title'] = 'Examples'
    data['examples'] = CHANDA.read_examples()
    return render_template('examples.html', data=data)

###############################################################################


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    port = 2490

    webapp.run(host=host, port=port, debug=True)
