import cv2
import numpy
img = cv2.imread('Q_s.png')
img=cv2.resize(img,(512,512))
#img = cv2.medianBlur(img, 9)                 # 模糊化，去除雜訊

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 轉成灰階

blurred = cv2.GaussianBlur(gray, (11, 11), 0)
binaryIMG = cv2.Canny(blurred, 20, 160)

cnts, _ = cv2.findContours(binaryIMG.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


# 绘制轮廓
#cv2.drawContours(img, [max_contour], -1, (0, 0, 255), 3)

cv2.drawContours(img,cnts,-1,(0,0,255),3)  
cv2.namedWindow("img", cv2.WINDOW_NORMAL) 
cv2.resizeWindow("img", 200, 200) 
cv2.imshow("img", img)  


cv2.waitKey(0)
cv2.destroyAllWindows()
# img 來源影像
# threshold1 門檻值，範圍 0～255
# threshold2 門檻值，範圍 0～255
# apertureSize 計算梯度的 kernel size，預設 3