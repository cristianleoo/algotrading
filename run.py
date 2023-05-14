import importlib

# list of libraries to check/install
libraries = ['flask']

# loop through libraries and check/install
for lib in libraries:
    try:
        importlib.import_module(lib)
        print(f"{lib} is already installed")
    except ImportError:
        #!pip install {lib}
        print(f"{lib} has been installed")

# import libraries
import requests
import json
import os
import re
from flask import Flask, request, render_template, redirect, url_for, Markup
import datetime

app = Flask("Stock Predictions", static_folder='static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
        
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='localhost', port=5001)