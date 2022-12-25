# Chandojñānam

Sanskrit meter identification and utilization system.

* Friendly user interface to display the scansion
* Fuzzy matches based on sequence matching,
* Capability to process entire file
* Ability to identify meters from images with the help of OCR.

Source code for https://sanskrit.iitk.ac.in/jnanasangraha/chanda/

## Installation

* Install Python requirements using

```pip install -r requirements.txt```

* Copy `settings.sample.py` to `settings.py` and configure settings.

**Note**: OCR systems need to be setup independently.

### Google OCR

* Link: https://pypi.org/project/google-drive-ocr/
* Follow setup instructions to setup a project on Google Cloud Platform

### Tesseract OCR

* Link: https://github.com/tesseract-ocr/
* Also install language files for Indian languages such as Sanskrit (`san`), Marathi (`mar`), Hindi (`hin`), Bengali (`ben`), Telugu (`tel`), Tamil (`tam`), Kannada (`kan`), Malayalam (`mal`), Gujarati (`guj`) etc.
* e.g.,
```sudo apt install tesseract-ocr-(san|mar|hin|ben|tel|tam|kan|mal|guj)```
