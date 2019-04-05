from time import sleep
from os import path, remove, listdir, mkdir
from shutil import copy2, rmtree
from datetime import datetime
from utility import logger



head_string = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Edge Computing Home Page</title>
    <br><br>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css" integrity="sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js" integrity="sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T" crossorigin="anonymous"></script>
</head>
<body>
<div class="container">
  <h2>Image Gallery</h2>
  <br><br>
  <div class="row">
  """

tail_string = """
    </div>
    <br>
    <div class="alert alert-success">

    <a href="{{ url_for('home') }}"> Click here to return Home</a>.
    </div>
  </div>
</body>
</html>
"""

row_string = """
  <div class="col-md-4">
    <div class="thumbnail">
      <a href="{}">
        <img src="{}" style="width:100%">
        <div class="caption">
          <p><center>{}</center></p>
        </div>
      </a>
    </div>
  </div>
"""
empty_gallery_string = """
    </div>
    <br>
    <div class="alert alert-success">

    <a href="{{ url_for('home') }}"> No Images. Click here to return Home</a>.
    </div>
  </div>
</body>
</html>
"""

def capture_image(cam, temp_dir):
    if not path.exists(temp_dir):
        mkdir(temp_dir)
    for count in range(1):
        sleep(2)
        filename = 'Image_{}.jpg'.format(datetime.now().strftime('%Y%m%d_%H%M%S'))
        image_path = path.join(temp_dir, filename)
        cam.capture(image_path)
        logger.info('\nCaptured photo {}\n'.format(filename))


def cleanup_local_dirs(temp_dir, static_dir, gallery_file):
    if path.exists(temp_dir):
        rmtree(temp_dir)
        logger.info("Removed temporary directory '{}'".format(temp_dir))
    else:
        logger.info("Temporary directory '{}' not found ".format(temp_dir))
    if path.exists(static_dir):
        rmtree(static_dir)
        logger.info("Removed static directory '{}'".format(static_dir))
    else:
        logger.info("Static directory '{}' not found ".format(static_dir))
    if path.exists(gallery_file):
        remove(gallery_file)
        logger.info("Removed gallery file '{}'".format(gallery_file))
    else:
        logger.info("Gallery File '{}' not found ".format(gallery_file))



def list_images(temp_dir, static_dir):
    if not path.exists(static_dir):
        mkdir(static_dir)
    if path.exists(temp_dir):
        with open('templates/list.html', 'w') as f:
            f.write(head_string)
        for filename in listdir(temp_dir):
            image_path = path.join(temp_dir, filename)
            copy2(image_path, static_dir)
            static_file = "static/{}".format(filename)
            actual_html_string = row_string.format(static_file, static_file, filename)
            with open('templates/list.html', 'a') as f:
                f.write(actual_html_string)
        with open('templates/list.html', 'a') as f:
            f.write(tail_string)
    else:
        with open('templates/list.html', 'w') as f:
            f.write(head_string)
            f.write(tail_string)




# list_images("C:/Users/anisaraf/Desktop/test", "C:/repos/happyface-edge-flask/static")
