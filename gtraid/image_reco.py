import os
from collections import namedtuple
import cv2
import yaml
import pytesseract
import numpy as np

RecognizedHitRecord = namedtuple('RecognizedHitRecord',
                                 ['name',               # Recognized name
                                  'damage',             # Recognized damage
                                  'original_img',       # Image of the record
                                  'name_rec_img',       # Image with name (used for recognition)
                                  'damage_rec_img',     # Image with damage (used for recognition)
                                  'party_img',          # Image with party
                                  'boss_img'])          # Image with boss


RecognizedImage = namedtuple('RecognizedImage',
                             ['hit_records'])           # Recognized hit records collected from the image


def load_crop_rects(config_file, width, height):
    """
    STEP 0. Load crop parameters for a given resolution
    :param config_file:
    :param width:
    :param height:
    :return:
    """

    print(f"load_crop_rects: Searching data for resolution {width}x{height}")
    with open(config_file, 'r') as stream:
        try:
            content = yaml.safe_load(stream)
            res_name = f"w{width}h{height}"
            if res_name not in content["resolutions"].keys():
                err = f"The resolution '{res_name}' is not found in file '{config_file}'"
                raise KeyError(err)
            print(f"load_crop_rects: found data for resolution {res_name}")
            return content["resolutions"][res_name]
        except yaml.YAMLError as exc:
            print(exc)


def crop_hits_window(img, crop_rect, debug=1, report=1):
    """
    Crops a window with member hits from overall screenshot
    :param img:
    :param crop_rect:
    :param debug:
    :param report:
    :return:
    """

    img_height, img_width, _ = img.shape
    print(f"crop_hits_window: img_height={img_height}, img_width={img_width}")

    x_start = crop_rect[0][0]
    y_start = crop_rect[0][1]
    x_end = crop_rect[1][0]
    y_end = crop_rect[1][1]

    crop = img[y_start:y_end, x_start:x_end]

    # Draw a rectangle with blue line borders of thickness of 2 px
    debug_img = img.copy()
    debug_img = cv2.rectangle(debug_img, crop_rect[0], crop_rect[1], (255, 0, 0), 2)

    # Save image for a report
    if report:
        cv2.imwrite("report/01_crop_hits_window__aim.jpg", debug_img)

    # show image
    if debug >= 2:
        cv2.imshow("crop_hits_window_debug", debug_img)
        cv2.imshow("crop_hits_window", crop)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return crop


def find_hits(img, hitbox_min_w,  hitbox_min_h, debug=1, report=1):
    """
    Find and extract hit images from hits list (hits list must be cropped)


    :param img: cv2 image (like after imgread)
    :param hitbox_min_h: Minimal height of hit box
    :param hitbox_min_w: Minimal width of hit box
    :param debug: 1 = just prints, 2 = show image processing
    :return:
    """

    # img = cv2.imread("../test_images/hits_crop.jpg")

    # make grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold image to remove as much as possible and leave frames
    mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)[1]

    # Cleanup by morphologyEX
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    close = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # >oO Debug output
    if debug >= 2:
        cv2.imshow("Masked image", mask)
        cv2.imshow("After morphologyEx", close)

    # Find contours (external only):
    # Since the cv2.findContours has been updated to return only 2 parameters
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"find_hits: found contours = {len(contours)}")

    if debug >= 2:
        # draw ALL contours on original image
        cv2.drawContours(img.copy(), contours, -1, (255, 0, 0), thickness=2)

    hit_images = []
    # Find bounding box and extract ROI
    for i, contour in enumerate(contours):

        x, y, width, height = cv2.boundingRect(contour)
        if height > hitbox_min_h and width > hitbox_min_w:

            # Crop by our contour
            crop = img[y:y+height, x:x+width]
            hit_images.append(crop)

            # >oO Debug output
            print(f"find_hits: saving: x={x}, y={y}, width={width}, height={height}")
            if debug >= 2:
                cv2.imshow(f"Contour{i}", crop)
        else:
            print(f"find_hits: skipping: x={x}, y={y}, width={width}, height={height}")

    # show image
    if debug >= 2:
        cv2.imshow("Original image", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if report:
        # Save image for a report
        cv2.imwrite("report/02_find_hits__mask.jpg", mask)
        img_with_contours = cv2.drawContours(img.copy(), contours, -1, (255, 0, 0), thickness=2)
        cv2.imwrite("report/02_find_hits__contours.jpg", img_with_contours)

    return hit_images


def crop_hit_image(img, img_index, name_rect, party_rect, damage_rect, boss_rect, report=1):
    """
    Crops hit image to pieces with name+time, party, damage, boss images
    :param img: image with hit (box)
    :param img_index: index of the hit image (used for report and debugging)
    :param name_rect: coordinates of name rectangle ((x_start, y_start), (x_end, y_end))
    :param party_rect: coordinates of party rectangle ((x_start, y_start), (x_end, y_end))
    :param damage_rect: coordinates of damage rectangle ((x_start, y_start), (x_end, y_end))
    :param boss_rect:  coordinates of boss rectangle ((x_start, y_start), (x_end, y_end))
    :param report: 1 - write report
    :return: name_img, party_img, boss_img, damage_img
    """
    img_height, img_width, img_channels = img.shape
    print(f"img.shape: img_height={img_height}, img_width={img_width}, img_channels={img_channels}")

    # Using cv2.rectangle() method
    # Draw a rectangle with blue line borders of thickness of 2 px
    debug_image = img.copy()
    debug_image = cv2.rectangle(debug_image, name_rect[0], name_rect[1], (255, 0, 0), 2)
    debug_image = cv2.rectangle(debug_image, party_rect[0], party_rect[1], (0, 255, 0), 2)
    debug_image = cv2.rectangle(debug_image, boss_rect[0], boss_rect[1], (0, 0, 255), 2)
    debug_image = cv2.rectangle(debug_image, damage_rect[0], damage_rect[1], (0, 255, 255), 2)

    # name image
    x_start, y_start, x_end, y_end = name_rect[0][0], name_rect[0][1], name_rect[1][0], name_rect[1][1]
    name_img = img[y_start:y_end, x_start:x_end]

    # party
    x_start, y_start, x_end, y_end = party_rect[0][0], party_rect[0][1], party_rect[1][0], party_rect[1][1]
    party_img = img[y_start:y_end, x_start:x_end]

    # boss
    x_start, y_start, x_end, y_end = boss_rect[0][0], boss_rect[0][1], boss_rect[1][0], boss_rect[1][1]
    boss_img = img[y_start:y_end, x_start:x_end]

    # damage
    x_start, y_start, x_end, y_end = damage_rect[0][0], damage_rect[0][1], damage_rect[1][0], damage_rect[1][1]
    damage_img = img[y_start:y_end, x_start:x_end]

    # TODO remove it to a sane place
    if report:
        # Save image for a report
        cv2.imwrite(f"report/03_crop_hit_{str(img_index).zfill(3)}.jpg", debug_image)
        cv2.imwrite(f"report/03_crop_hit_name_img_{str(img_index).zfill(3)}.jpg", name_img)
        cv2.imwrite(f"report/03_crop_hit_party_img_{str(img_index).zfill(3)}.jpg", party_img)
        cv2.imwrite(f"report/03_crop_hit_boss_img_{str(img_index).zfill(3)}.jpg", boss_img)
        cv2.imwrite(f"report/03_crop_hit_damage_img_{str(img_index).zfill(3)}.jpg", damage_img)

    return name_img, party_img, boss_img, damage_img


def recognize_damage(img, debug=0):
    """
    Recognizes damage from damage box
    :param img: Image
    :param debug: 2 - show images, 1 - print, 0 - nothing
    :return: image used for recognition and name
    """

    # create grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold image to remove noise and create an inverted mask with with OTSU
    mask = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)[0]

    # By default OpenCV stores images in BGR format and since pytesseract assumes RGB format,
    # we need to convert from BGR to RGB format/mode:
    img_rgb = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)

    damage_str = pytesseract.image_to_string(img_rgb).replace("\n\f,", "")
    print("recognize_damage: Damage is:", damage_str)

    if debug >= 2:
        cv2.imshow("Original", img)
        cv2.imshow("Masking damage", mask)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return mask, damage_str


def autocrop(image, threshold=0):
    """Crops any edges below or equal to threshold

    Crops blank image to 1x1.

    Returns cropped image.

    """
    if len(image.shape) == 3:
        flatImage = np.max(image, 2)
    else:
        flatImage = image
    assert len(flatImage.shape) == 2

    rows = np.where(np.max(flatImage, 0) > threshold)[0]
    if rows.size:
        cols = np.where(np.max(flatImage, 1) > threshold)[0]
        # image = image[cols[0]: cols[-1] + 1, rows[0]: rows[-1] + 1]
        return cols[0], cols[-1] + 1, rows[0], rows[-1] + 1
    else:
        # image = image[:1, :1]
        return 0, 1, 0, 1


def recognize_name(img, debug=0):
    """
    Recognizes name
    :param img:
    :param debug:
    :return:
    """

    # create grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold image to remove noise and create an inverted mask with with OTSU
    only_name_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]

    # This mask removes time information, but name is difficult to recognize
    # so we use autocrop function, to figure the place where name ends!
    crop_rect = autocrop(only_name_mask)

    # Now we crop image removing not needed time information
    crop_name_img = gray[:, :crop_rect[3]+10]

    # This mask makes recognizing english and korean names easier
    mask2 = cv2.threshold(crop_name_img, 130, 255, cv2.THRESH_BINARY)[1]

    # Invert image to make it black on white
    reco_image = 255-mask2

    # recognize the image
    name = pytesseract.image_to_string(reco_image, lang="kor+eng")
    print(f"Name is: {name}")

    if debug >= 2:
        cv2.imshow("Original", img)
        cv2.imshow("Masking", only_name_mask)
        cv2.imshow("Crop", crop_name_img)
        cv2.imshow("Time mask", reco_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return reco_image, name


def recognize_image(img_path, crop_rects, report=1, debug=1):
    """
    Recognizes the image
    :param img_path:
    :param crop_rects:
    :param report:
    :param debug:
    :return:
    """



    # 0. Open image
    img = img_path

    if img is None:
        error = f"Not able to open image '{img_path}'"
        raise ValueError(error)

    # 1. Crop hit window
    img_height, img_width, _ = img.shape

    crop_hits_dim = ((crop_rects["hits_window"]["x_start"], crop_rects["hits_window"]["y_start"]),
                     (crop_rects["hits_window"]["x_end"], crop_rects["hits_window"]["y_end"]))

    raid_hits_img = crop_hits_window(img, crop_hits_dim, debug=debug)

    # 2. Find hits images
    hit_images = find_hits(raid_hits_img,
                           crop_rects["hit_image"]["min_width"],
                           crop_rects["hit_image"]["min_height"],
                           debug=0)

    it_records = []

    # 3. Crop hits image to pieces
    for index, hit_image in enumerate(hit_images):
        name_rect = ((crop_rects["hit_image"]["name_rect"]["x_start"],
                      crop_rects["hit_image"]["name_rect"]["y_start"]),
                     (crop_rects["hit_image"]["name_rect"]["x_end"],
                      crop_rects["hit_image"]["name_rect"]["y_end"]))
        party_rect = ((crop_rects["hit_image"]["party_rect"]["x_start"],
                       crop_rects["hit_image"]["party_rect"]["y_start"]),
                      (crop_rects["hit_image"]["party_rect"]["x_end"],
                       crop_rects["hit_image"]["party_rect"]["y_end"]))
        damage_rect = ((crop_rects["hit_image"]["damage_rect"]["x_start"],
                        crop_rects["hit_image"]["damage_rect"]["y_start"]),
                       (crop_rects["hit_image"]["damage_rect"]["x_end"],
                        crop_rects["hit_image"]["damage_rect"]["y_end"]))
        boss_rect = ((crop_rects["hit_image"]["boss_rect"]["x_start"],
                      crop_rects["hit_image"]["boss_rect"]["y_start"]),
                     (crop_rects["hit_image"]["boss_rect"]["x_end"],
                      crop_rects["hit_image"]["boss_rect"]["y_end"]))

        name_img, party_img, boss_img, damage_img = crop_hit_image(hit_image, index, name_rect, party_rect,
                                                                   damage_rect, boss_rect)
        name_rec_img, name = recognize_name(name_img)
        damage_rec_img, damage = recognize_damage(damage_img)

    # forming result
    result = RecognizedImage()
    result.h

if __name__ == "__main__":

    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if not os.path.isdir("report"):
        os.mkdir("report")

    #img = cv2.imread("../test_images/Guardian Tales_2021-05-31-22-12-10.jpg")
    #img = cv2.imread("../test_images/Guardian Tales_2021-06-01-18-57-13.jpg")

    img = cv2.imread("../test_images/rock/Screenshot_2021-05-31-23-32-40.png")
    #img = cv2.imread("../test_images/rock/Screenshot_2021-05-31-23-32-48.png")
    #img = cv2.imread("../test_images/rock/Screenshot_2021-05-31-23-31-31.png")

    if img is None:
        print("ERROR, was not able to open image")
        exit(1)


    img_height, img_width, _ = img.shape
    crop_rects = load_crop_rects("../dimensions.yaml", img_width, img_height)

    crop_hits_dim = ((crop_rects["hits_window"]["x_start"], crop_rects["hits_window"]["y_start"]),
                     (crop_rects["hits_window"]["x_end"], crop_rects["hits_window"]["y_end"]))

    raid_hits_img = crop_hits_window(img, crop_hits_dim, debug=0)


    hit_images = find_hits(raid_hits_img, crop_rects["hit_image"]["min_width"], crop_rects["hit_image"]["min_height"], debug=0)

    for index, hit_image in enumerate(hit_images):
        name_rect = ((crop_rects["hit_image"]["name_rect"]["x_start"],
                      crop_rects["hit_image"]["name_rect"]["y_start"]),
                     (crop_rects["hit_image"]["name_rect"]["x_end"],
                      crop_rects["hit_image"]["name_rect"]["y_end"]))
        party_rect = ((crop_rects["hit_image"]["party_rect"]["x_start"],
                       crop_rects["hit_image"]["party_rect"]["y_start"]),
                      (crop_rects["hit_image"]["party_rect"]["x_end"],
                       crop_rects["hit_image"]["party_rect"]["y_end"]))
        damage_rect = ((crop_rects["hit_image"]["damage_rect"]["x_start"],
                        crop_rects["hit_image"]["damage_rect"]["y_start"]),
                       (crop_rects["hit_image"]["damage_rect"]["x_end"],
                        crop_rects["hit_image"]["damage_rect"]["y_end"]))
        boss_rect = ((crop_rects["hit_image"]["boss_rect"]["x_start"],
                      crop_rects["hit_image"]["boss_rect"]["y_start"]),
                     (crop_rects["hit_image"]["boss_rect"]["x_end"],
                      crop_rects["hit_image"]["boss_rect"]["y_end"]))

        name_img, party_img, boss_img, damage_img = crop_hit_image(hit_image, index, name_rect, party_rect, damage_rect, boss_rect)
        recognize_name(name_img)
        #break

    #cv2.waitKey(0)
    #cv2.destroyAllWindows()



