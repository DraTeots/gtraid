import argparse
import math
import os
import io

import cv2

import pytesseract
from gtraid import recognize_screenshot, DimensionsFile, RecognizedImage, RecognizedHitRecord
import xlsxwriter
import glob

from gtraid.image_reco import auto_crop

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('inputs', nargs='+', help="File name (wildcards allowed)")
    parser.add_argument("-d", "--debug", type=int, choices=[0, 1, 2], default=0,
                        help="Enable debugging output. 0-none, 1-prings, 2-showimg")
    parser.add_argument("-r", "--report", default="report", help="Report folder (set blank for no report)")
    parser.add_argument("-o", "--output", default="result.xlsx", help="File name of resulting xlsx")
    parser.add_argument("-t", "--tesseract", default=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                        help="Full path to tesseract.exe")

    args = parser.parse_args()

    # Setup tesseract executable
    pytesseract.pytesseract.tesseract_cmd = args.tesseract

    # Dimensions file
    dimensions_file = DimensionsFile('dimensions.yaml')

    # Create "report" directory
    if args.report and not os.path.isdir(args.report):
        os.mkdir(args.report)

    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook(args.output)
    worksheet = workbook.add_worksheet()

    # Parsed name column
    worksheet.set_column('A:A', 15)

    # Damage column
    worksheet.set_column('C:C', 15)

    # Format output for a damage
    damage_num_format = workbook.add_format({'num_format': '#,##0.', 'align': 'left'})
    damage_exists_format = workbook.add_format({'num_format': '#,##0.', 'bg_color': '#ffb3b3', 'align': 'left'})   # #ffb3b3 - light red

    # this map is used to track doublicated hits
    damage_name_map = {}

    # iterable showing current row to fill
    cur_row = 1

    # width for pictures column
    max_name_width = 100
    max_damage_width = 100
    max_party_width = 100
    max_boss_width = 100
    max_hit_width = 100

    worksheet.set_column_pixels("B:B", max_name_width)      # Name image column
    worksheet.set_column_pixels("D:D", max_damage_width)    # Damage image  column
    worksheet.set_column_pixels("E:E", max_party_width)     # Party image column
    worksheet.set_column_pixels("F:F", max_boss_width)      # Boss image column
    worksheet.set_column_pixels("G:G", 400)
    worksheet.set_column_pixels("I:I", max_hit_width)

    # What files to process
    files = []
    for user_input in args.inputs:
        # use Glob to convert something like some_dir/* to file names
        files.extend([file_path for file_path in glob.glob(user_input)])

    # Iterate over screenshot files
    for file_name in files:
        print("\n=====================================")
        print(" P R O C E S S I N G :")
        print(file_name)

        img = cv2.imread(file_name)
        if img is None:
            print(f"(!!!) ERROR (!!!): Can't open file: {file_name}")
            continue

        crop_rects = dimensions_file.get_crop_rects(img)
        image_base_name = os.path.splitext(os.path.basename(file_name))[0]

        # do we need to fill a report?
        report_path = f"{args.report}/{image_base_name}_" if args.report else ""

        # RECOGNIZE SCREENSHOT
        result = recognize_screenshot(img, crop_rects, report_path=report_path, debug=args.debug)
        print(f"Recognized f{len(result.hit_records)} hits")

        # Iterate over hits
        for hit_index, hit_record in enumerate(result.hit_records):
            print(f"  {hit_record.name} {hit_record.damage}")

            # Add name to worksheet
            worksheet.write(f'A{cur_row}', hit_record.name)

            # Parse damage and add to worksheet
            if hit_record.damage:
                try:
                    damage = int(hit_record.damage.replace(',', ''))

                    damage_name_pair = hit_record.damage + hit_record.name

                    # There was no such damage before for this name?
                    if damage_name_pair not in damage_name_map.keys():
                        # Just add to the cell then
                        damage_name_map[damage_name_pair] = damage
                        worksheet.write_number(f'C{cur_row}', damage, damage_num_format)
                    else:
                        # Probably image overlap!
                        worksheet.write(f'C{cur_row}', damage, damage_exists_format)
                except ValueError as ex:
                    print(f"WARNING: can't convert damage '{hit_record.damage}' to integer! {ex}")
            else:
                print(f"WARNING: Damage is empty for hit# {hit_index} name: '{hit_record.name}'")

            # NAME image
            name_img = 255 - auto_crop(255-hit_record.name_rec_img)   # crop empty edges
            name_img = cv2.resize(name_img, (0, 0), fx=0.4, fy=0.4)  # resize to 40%
            name_height, name_width = name_img.shape
            is_success, buffer = cv2.imencode(".jpg", name_img)
            if name_width > max_name_width:
                max_name_width = name_width
                worksheet.set_column_pixels("B:B", max_name_width+10)
            worksheet.insert_image(f'B{cur_row}', f'name{cur_row}', {'image_data': io.BytesIO(buffer), 'object_position': 1})

            # Damage image
            damage_img = 255 - auto_crop(255 - hit_record.damage_rec_img)  # crop empty edges
            damage_img = cv2.resize(damage_img, (0, 0), fx=0.5, fy=0.5)      # resize to 50%
            damage_height, damage_width = damage_img.shape
            is_success, buffer = cv2.imencode(".jpg", damage_img)
            if damage_width > max_damage_width:
                max_damage_width = damage_width
                worksheet.set_column_pixels("D:D", max_damage_width+10)
            worksheet.insert_image(f'D{cur_row}', f'damage{cur_row}', {'image_data': io.BytesIO(buffer)})

            # Party image
            party_img = cv2.resize(hit_record.party_img, (0, 0), fx=0.5, fy=0.5)
            party_height, party_width, _ = party_img.shape
            is_success, buffer = cv2.imencode(".jpg", party_img)
            if party_width > max_party_width:
                max_party_width = party_width
                worksheet.set_column_pixels("E:E", max_party_width+10)
            worksheet.insert_image(f'E{cur_row}', f'party{cur_row}', {'image_data': io.BytesIO(buffer)})

            # Boss image
            boss_img = cv2.resize(hit_record.boss_img, (0, 0), fx=0.5, fy=0.5)
            boss_height, boss_width, _ = boss_img.shape
            is_success, buffer = cv2.imencode(".jpg", boss_img)
            if boss_width > max_boss_width:
                max_boss_width = boss_width
                worksheet.set_column_pixels("F:F", max_boss_width+10)
            worksheet.insert_image(f'F{cur_row}', f'boss{cur_row}', {'image_data': io.BytesIO(buffer)})

            # Hit image
            hit_img = cv2.resize(hit_record.original_img, (0, 0), fx=0.7, fy=0.7)  # resize to 70%
            hit_height, hit_width, _ = hit_img.shape
            hit_image_scale = 0.3                       # we will scale in excel
            hit_width = hit_width*hit_image_scale
            hit_height = hit_height*hit_image_scale
            is_success, buffer = cv2.imencode(".jpg", hit_img)
            if hit_width > max_hit_width:
                max_hit_width = hit_width
                worksheet.set_column_pixels("I:I", max_hit_width + 10)
            worksheet.insert_image(f'I{cur_row}', f'hit{cur_row}', {'image_data': io.BytesIO(buffer), 'x_scale': hit_image_scale, 'y_scale': hit_image_scale})

            # Now what is row height?
            row_height = max(name_height, damage_height, party_height, boss_height, hit_height)
            worksheet.set_row_pixels(cur_row - 1, row_height)

            # Add file name
            worksheet.write(f'G{cur_row}', image_base_name)
            worksheet.write(f'H{cur_row}', hit_index)

            cur_row += 1


    # close work book
    workbook.close()





