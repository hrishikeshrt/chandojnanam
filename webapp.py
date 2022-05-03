#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 16:11:35 2019

@author: Hrishikesh Terdalkar
"""

import json
import datetime

from flask import Flask, request, render_template, flash  # , url_for, redirect
from flask_uploads import (
    UploadSet, IMAGES, TEXT, configure_uploads, patch_request_class
)

import pytesseract
from google_drive_ocr import GoogleOCRApplication

import chanda
from settings import (
    DATA_PATH, TMP_PATH,
    APPLICATION_NAME, SECRET_KEY,
    CLIENT_SECRET
)

###############################################################################

Chanda = chanda.Chanda(DATA_PATH)

# Upload Paths
TMP_PATH.mkdir(parents=True, exist_ok=True)
PHOTOS_PATH = TMP_PATH
TEXTS_PATH = TMP_PATH

# OCR
GoogleOCR = GoogleOCRApplication(
    client_secret=CLIENT_SECRET,
    temporary_upload=True
)

###############################################################################

webapp = Flask(APPLICATION_NAME,
               template_folder='templates',
               static_folder='static')
webapp.secret_key = SECRET_KEY

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
    }


@webapp.route('/line', methods=['GET', 'POST'], strict_slashes=False)
def identify_line():
    data = {}
    data['title'] = 'Identify from Line'
    if request.method == 'POST':
        data['text'] = request.form['input_text']
        webapp.logger.info(f"INPUT: {data['text']}")
        try:
            result = Chanda.identify_line(data['text'], fuzzy=True)
            data['result'] = result
        except Exception as e:
            flash(str(e))
        # data['result'] = json.dumps(result, ensure_ascii=False, indent=2)
    return render_template('line.html', data=data)


@webapp.route('/image', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_image():
    data = {}
    data['title'] = 'Identify from Image'
    data['engines'] = {
        'google': 'Google OCR',
        'tesseract': 'Tesseract OCR'
    }
    data['engine'] = 'tesseract'

    if request.method == 'POST':
        data['text'] = request.form.get('input_text', '')

        if request.files['image_file'].filename:
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
                tesseract_config = '-l san'
                data['text'] = pytesseract.image_to_string(
                    str(filepath),
                    config=tesseract_config
                )
        else:
            if not data['text']:
                flash("Please select an image file.")

        webapp.logger.info(f"INPUT: {data['text']}")
        try:
            result = Chanda.identify_from_text(data['text'], fuzzy=True)
            data['result'] = result
        except Exception as e:
            flash(str(e))
        # data['result'] = json.dumps(result, ensure_ascii=False, indent=2)
    return render_template('image_file.html', data=data)


@webapp.route('/file', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_file():
    data = {}
    data['title'] = 'Identify from Verse'
    if request.method == 'POST':
        data['text'] = request.form.get('input_text', '')

        if request.files['text_file'].filename:
            filename = texts.save(request.files['text_file'])
            filepath = TEXTS_PATH / filename
            try:
                result = Chanda.analyse(filepath, fuzzy=True)
                data['result'] = json.dumps(result, indent=True, ensure_ascii=False)
            except Exception as e:
                flash(str(e))
        else:
            flash("Please select a text file to analyse.")
    return render_template('text_file.html', data=data)


@webapp.route('/verse', methods=['GET', 'POST'], strict_slashes=False)
def identify_from_text():
    data = {}
    data['title'] = 'Identify from Verse'
    if request.method == 'POST':
        data['text'] = request.form['input_text']
        webapp.logger.info(f"INPUT: {data['text']}")
        try:
            result = Chanda.identify_from_text(data['text'], fuzzy=True)
            data['result'] = result
        except Exception as e:
            flash(str(e))
        # data['result'] = json.dumps(result, ensure_ascii=False, indent=2)
    return render_template('verse.html', data=data)


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
    data['examples'] = Chanda.read_examples()
    return render_template('examples.html', data=data)

###############################################################################


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    port = 2490

    webapp.run(host=host, port=port, debug=True)
