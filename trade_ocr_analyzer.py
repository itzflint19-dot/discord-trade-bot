import pytesseract
import cv2
import numpy as np

def analyze_trade_image(image_bytes):
    image_array = np.asarray(bytearray(image_bytes), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    raw_text = pytesseract.image_to_string(gray)
    print("\n[OCR RAW TEXT]\n", raw_text)

    items_given = ["Item A", "Item B"]
    items_received = ["Item C"]
    rap_given = 10500
    rap_received = 12000
    value_given = 11000
    value_received = 13500

    gain = value_received - value_given
    if gain > 0:
        verdict = "Accept"
    elif gain < -1000:
        verdict = "Decline"
    else:
        verdict = "Consider"

    return {
        'items_given': items_given,
        'items_received': items_received,
        'rap_given': rap_given,
        'rap_received': rap_received,
        'value_given': value_given,
        'value_received': value_received,
        'verdict': verdict
    }
