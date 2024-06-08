import cv2

img = cv2.imread('Qe.png')
img = cv2.resize(img, (512, 512))
blur = cv2.medianBlur(img, 9)                 # 模糊化，去除雜訊

gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)  # 轉成灰階
gray = cv2.GaussianBlur(gray, (15, 15), 0)

ret, binary = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)  #二值化
binary = cv2.Canny(binary, 40, 180)
# 設定kernel滾動作用的像素範圍
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
# 膨脹操作
dilated = cv2.dilate(binary, kernel)
# 腐蝕操作
eroded = cv2.erode(dilated, kernel)

print(eroded.size)
img_cp = img.copy()

cv2.imshow("eroded", eroded)
cv2.waitKey(0)
cv2.destroyAllWindows()  
# 提取 alpha 通道
#alpha_channel = img[:, :, 3]

# 计算非透明像素的数量
# non_transparent_pixels = cv2.countNonZero(alpha_channel)

# print("非透明像素的数量:", non_transparent_pixels)