from flask import Flask, render_template, redirect, url_for
from tempfile import gettempdir
from os import path, mkdir, listdir, remove
from picamera import PiCamera
from handler.cam_handler import capture_image, cleanup_local_dirs, list_images
from handler.img_handler import process_image
from handler.es_handler import create_indices
from handler.db_handler import delete_items_from_db
from handler.s3_handler import delete_objects
from utility import logger

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcd1234'
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

temp_dir = "{}/happyface".format(gettempdir())
static_dir = "static"
gallery_file = 'templates/list.html'

cam = PiCamera()
cam.resolution = (2592, 1944)

if not path.exists(temp_dir):
    mkdir(temp_dir)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/new_index')
def new_index():
    create_indices()
    return render_template('new_index.html')


@app.route('/capture')
def capture():
    capture_image(cam, temp_dir)
    return render_template('captured.html')


@app.route('/process')
def process():
    for img_file in listdir(temp_dir):
        tmp_file = path.join(temp_dir, img_file)
        process_image(tmp_file)
        remove(tmp_file)
    return render_template('processed.html')


@app.route('/gallery')
def gallery():
    list_images(temp_dir, static_dir)
    return render_template('list.html')


@app.route('/cleanup')
def cleanup():
    logger.info("\nStarting Cleanup...")
    cleanup_local_dirs(temp_dir, static_dir, gallery_file)
    delete_objects()
    delete_items_from_db()
    logger.info("Cleanup Completed\n")
    return render_template('cleanup.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
