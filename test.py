import os
import cv2

import pytesseract
from gtraid import recognize_screenshot, DimensionsFile



if __name__ == "__main__":

    # Set it to your tesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Current script dir is the root
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # create a report folder
    if not os.path.isdir("report"):
        os.mkdir("report")

    # open sample image
    # https://yangcha.github.io/iview/iview.html
    #image_path = os.path.join(dir_path, 'test_images', 'rock',  'Screenshot_2021-05-31-23-32-40.png')
    #image_path = os.path.join(dir_path, 'test_images', 't2.jpg')
    image_path = os.path.join(dir_path, 'test_images', '1440_720x.png')
    img = cv2.imread(image_path)

    if img is None:
        print(f"ERROR, was not able to open image '{image_path}'")
        exit(1)

    # Open crop rectangles for current resolution
    img_height, img_width, _ = img.shape
    dimensions = DimensionsFile("dimensions.yaml")

    # Recognizes screenshot with debugging
    recognize_screenshot(img, dimensions.get_crop_rects(img), report_path="", debug=2)
