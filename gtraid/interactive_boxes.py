import cv2
import numpy as np

drawing = False # True if mouse is pressed
mode = True # if True, draw rectangle. Press 'm' to toggle to curve
ix, iy = -1, -1

# mouse callback function
def draw_circle(event, x, y, flags, param):
    global ix, iy, drawing, mode, overlay, output, alpha
    overlay = img.copy()
    output = img.copy()
    alpha = 0.5

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            if mode == True:
                cv2.rectangle(overlay, (ix, iy), (x, y), (0, 255, 0), -1)
                cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, img2)
                cv2.imshow('image', img2)
            else:
                cv2.circle(overlay, (x,y),5,(0,0,255),-1)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        if mode == True:
            cv2.rectangle(overlay, (ix, iy), (x, y), (0, 255, 0), -1)
            cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, img)
            print(f"(ix={ix}, iy={iy}), (x={x}, y={y})")

        else:
            cv2.circle(overlay, (x, y), 5, (0, 0, 255), -1)



##img = np.zeros((512, 512, 3), np.uint8)
# Get our image
img = cv2.imread("../test_images/Guardian Tales_2021-05-31-22-12-10.jpg", 1)
img = cv2.resize(img, (0, 0), fx=0.7, fy=0.7)
img2 = img.copy()

#make cv2 windows, set mouse callback
cv2.namedWindow('image')
cv2.setMouseCallback('image', draw_circle)

#cv2.namedWindow('image', cv2.WINDOW_NORMAL)
#cv2.resizeWindow('image', 600,600)

while(1):
    cv2.imshow('image', img2)

    # This is where we get the keyboard input
    # Then check if it's "m" (if so, toggle the drawing mode)
    k = cv2.waitKey(1) & 0xFF
    if k == ord('m'):
        mode = not mode
    elif k == 27:
        break

cv2.destroyAllWindows()