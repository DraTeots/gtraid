import cv2
import pytesseract

img_cv = cv2.imread('../test_images/damage_crop.jpg')

## create grayscale
gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

## threshold image to remove noise and create an inverted mask with with OTSU
mask = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)[1]

cv2.imshow("Original", img_cv)
cv2.imshow("Masking damage", mask)


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'
# r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# By default OpenCV stores images in BGR format and since pytesseract assumes RGB format,
# we need to convert from BGR to RGB format/mode:
img_rgb = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
print("Damage is:", pytesseract.image_to_string(img_rgb))

cv2.waitKey(0)
cv2.destroyAllWindows()