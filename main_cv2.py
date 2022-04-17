import datetime
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def addText(img, text, left, top, textColor=(0, 255, 0), textSize=20):
    # cv.putText() 不支持中文，因此采用此方法
    if isinstance(img, np.ndarray):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))  # 创建一个可以在给定图像上绘图的对象
        draw = ImageDraw.Draw(img)  # 字体的格式
        fontStyle = ImageFont.truetype(r"font/simsun.ttc", textSize, encoding="utf-8")  # 绘制文本
        draw.text((left, top), text, textColor, font=fontStyle)  # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def cutText(str_txt, start=None, stop=None):
    # 按GBK编码切割字符串
    cut_bytes = str_txt.encode('gbk', errors='ignore')
    try:
        cut_tmp = cut_bytes[start:stop]
    except UnicodeDecodeError:  # 遇到编码错误，则是切到中文字符中间
        cut_tmp = cut_bytes[start + 1:stop]
    cut_res = cut_tmp.decode('gbk', errors='ignore')
    if cut_res not in str_txt:  # 也有可能切到中文字符中间，但还是能编码，判断编码是否正确
        cut_tmp = cut_bytes[start + 1:stop]
        cut_res = cut_tmp.decode('gbk', errors='ignore')
    return cut_res


def walkFile(p):  # 遍历整个文件夹
    v_file = []
    # 不支持ts格式
    fix = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv']
    # fix = ["ts"]
    for root, dirs, files in os.walk(p):
        # root 表示当前正在访问的文件夹路径
        # dirs 表示该文件夹下的子目录名list
        # files 表示该文件夹下的文件list
        # 遍历文件
        for file in files:
            # print(os.path.join(root, f))
            if str(file.split('.')[-1].lower()) in fix:
                v_file.append(os.path.join(root, file))
    print(v_file)
    return v_file


def videoCapture(videoPath, forceJpg=False):
    global err_file
    print(f"视频路径：{videoPath}")
    if not os.path.exists(videoPath):
        print("视频不存在，")
        return
    jpgPath = os.path.splitext(videoPath)[0] + ".jpg"
    if os.path.exists(jpgPath) and (forceJpg is False):
        print("图片已存在，")
        return
    cap = cv2.VideoCapture(videoPath)
    if not cap.isOpened():
        print("视频无法打开，")
        return
    # 获取视频基本信息
    fps = int(cap.get(cv2.CAP_PROP_FPS))  # 帧率
    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # 宽度
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 高度
    frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 总图像帧数
    durationSec = round(frameCount / fps)  # 持续时间，秒
    duration = str(datetime.timedelta(seconds=durationSec))  # 持续时间，时分秒
    videoSize = os.path.getsize(videoPath)  # 文件大小，Byte
    if videoSize < 2 ** 30:  # 如果文件大小小于1GB
        fileSize = str(round(os.path.getsize(videoPath) / (2 ** 20), 2)) + 'MB'  # 单位MB
    else:
        fileSize = str(round(os.path.getsize(videoPath) / (2 ** 30), 2)) + 'GB'  # 单位GB
    picNum = 16
    # cFrame保存截图的帧位置，先取靠前一张，靠后一张，然后根据需要的图片数截取中间的图片
    cFrame = [round(frameCount * 0.01), round(frameCount * 0.99)]
    for a in range(1, picNum - 1):
        cFrame.append(round(frameCount * 0.98 / (picNum - 1) * a))
    cFrame.sort()
    print(f"截取帧：{cFrame}")
    img_frame = []
    print("截取时间: ", end='')
    for a in cFrame:
        cap.set(cv2.CAP_PROP_POS_FRAMES, a)  # 截取指定帧数
        ret, frame = cap.read()
        if frameWidth < frameHeight:  # 如果长宽比大于1，即竖屏视频，截图旋转90°
            try:
                img = np.rot90(frame)
            except ValueError:
                err_file.append(videoPath)
                print("文件rot90出错！！")
                return
        else:
            img = frame
        try:
            img = cv2.resize(img, (335, 204), interpolation=cv2.INTER_AREA)
        except cv2.error:
            err_file.append(videoPath)
            print("文件损坏或编码不支持！！")
            return
        timeText = str(datetime.timedelta(seconds=round(a / fps)))
        print(f"#{timeText} ", end='')
        # 时间戳仿阴影效果
        img = cv2.putText(img, timeText, (round(335 * 0.72) - 1, round(204 * 0.9) + 1), cv2.LINE_AA, 0.7,
                          (0, 0, 0), 2)
        img = cv2.putText(img, timeText, (round(335 * 0.72) + 1, round(204 * 0.9) + 1), cv2.LINE_AA, 0.7,
                          (0, 0, 0), 2)
        img = cv2.putText(img, timeText, (round(335 * 0.72) + 1, round(204 * 0.9) - 1), cv2.LINE_AA, 0.7,
                          (0, 0, 0), 2)
        img = cv2.putText(img, timeText, (round(335 * 0.72) - 1, round(204 * 0.9) - 1), cv2.LINE_AA, 0.7,
                          (0, 0, 0), 2)
        img = cv2.putText(img, timeText, (round(335 * 0.72), round(204 * 0.9)), cv2.LINE_AA, 0.7,
                          (220, 220, 220), 2)
        img_frame.append(img)  # 分帧读取视频
    print('', end='\n')
    cap.release()
    print('图片截取完成。')
    backImg = cv2.imread("background_icon.jpg")
    backImg_h = backImg.shape[0]
    backImg_w = backImg.shape[1]
    # icon = cv2.imread("icon.png")
    # backImg[20:234, 20:234] = icon
    # 文件名过长，换行处理
    vPath = videoPath.split('\\')[-1]
    if len(vPath.encode('gbk', errors='ignore')) > 130:
        vPath = cutText(vPath, 0, 65) + '\n          ' + cutText(vPath, 65, 100) + '...' + cutText(vPath, -26) + '\n\n'
    elif len(vPath.encode('gbk', errors='ignore')) > 65:
        vPath = cutText(vPath, 0, 65) + '\n          ' + cutText(vPath, 65) + '\n\n'
    else:
        vPath = vPath + '\n\n\n'
    videoInfo = '文件名称：' + vPath + '文件大小：' + fileSize + '     视频时长：' + duration + '     视频尺寸：' + str(
        frameWidth) + '×' + str(frameHeight)
    targetImg = addText(backImg, videoInfo, round(backImg_w * 0.17), round(backImg_h * 0.055), (10, 10, 10), 30)
    print('视频信息文本添加完成。')
    img_h = 224
    img_w = 20
    for a in range(picNum):
        targetImg[img_h:(img_h + 204), img_w:(img_w + 335)] = img_frame[a]  # 背景图像[左边像素:右边, 上边:下边] = 截取图像
        img_w = img_w + 355
        if img_w >= 1440:  # 如果截图排列超出边框，换下一行
            img_h = img_h + 214
            img_w = 20
    print('视频截图排列添加完成。')
    cv2.imencode('.jpg', targetImg)[1].tofile(jpgPath)  # encode()函数返回两个值;写入成功返回Ture，另一个值为数组.
    print(f'视频截图保存在:{jpgPath}')


def main(p, mode=2):
    if mode == 1:
        path_list = walkFile(p)
        list_len = len(path_list)
        i = 1
        for pathVideo in path_list:
            print(f'\n◉ 进度: {round(i / list_len * 100, 1)}% ({i}/{list_len})')
            videoCapture(videoPath=pathVideo, forceJpg=False)
            i = i + 1
        print(f"\n出错文件，共{len(err_file)}个：{err_file}")
    elif mode == 2:
        for pathVideo in p:
            videoCapture(videoPath=pathVideo, forceJpg=True)
        print(f"出错文件，共{len(err_file)}个：{err_file}")
    else:
        print("Mode error")


if __name__ == '__main__':
    err_file = []
    path = [
        r'C:\Users\admin\Desktop\1.mp4',
        r'C:\Users\admin\Desktop\2.mp4',
        r'C:\Users\admin\Desktop\3.mp4'
    ]
    # path = r'C:\Users\admin\Desktop'
    # mode1文件夹遍历，mode2单个或多个指定文件，有出错文件可以复制出错结果，用mode2再试
    main(path, mode=2)
