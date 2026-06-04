import cv2
import matplotlib.pyplot as plt

# Load and show the image
img = cv2.imread('your_image.png')
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.title('Original Image')
plt.show()

# Preprocess and show
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
plt.imshow(thresh, cmap='gray')
plt.title('Thresholded Image')
plt.show()

# Run OCR and print output
import pytesseract
text = pytesseract.image_to_string(thresh)
print("OCR Output:", text)