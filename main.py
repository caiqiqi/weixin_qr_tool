#coding=utf-8
import os
import time
import shutil
import requests
import json
import zipfile
from PIL import Image


URL_QR_API      = "http://qr.topscan.com/api.php?text="

URL_API         = "https://api.anquanke.com/data/v1/posts"    #获取当天所有文章(json格式)
URL_ARTICLE_PRE = "https://www.anquanke.com/post/id/{}"

DIR_BASE     = u"download/base"
DIR_BASE_re  = u"download/base_re"
DIR_QR       = u"download/qr"
DIR_QR_THUMB = u"gen/qr_thumb"
DIR_COMB     = u"gen/combined"


PIC_SUFFIX    = "{}.png"
FILE_BASE     = DIR_BASE        + "/" + PIC_SUFFIX
FILE_BASE_RE  = DIR_BASE_re     + "/" + PIC_SUFFIX
FILE_QR       = DIR_QR          + "/" + PIC_SUFFIX
FILE_QR_THUMB = DIR_QR_THUMB    + "/" + PIC_SUFFIX
FILE_COMB     = DIR_COMB        + "/" + PIC_SUFFIX


IS_DEMO         = False
_s              = requests.Session()


class JSONObject:
    def __init__(self, d):
        self.__dict__ = d

def print_(n=30):
    print "-" * n

def log(p_log=""):
    print "[*] " + p_log

def fetch_img_and_save(p_session, p_url, p_file_out):
    '''GET图片，存在本地
    '''
    r0 = p_session.get(p_url)
    with open(p_file_out, 'wb') as f:
        f.write(r0.content)

def resize_qr(p_img, rate_x, rate_y, p_out_file):  
    '''按照宽度进行所需比例缩放
    '''
    (x, y) = p_img.size   
    x_s = x/rate_x
    y_s = y/rate_y
    out = p_img.resize((x_s, y_s), Image.ANTIALIAS)   
    out.save(p_out_file)
    return out


def resize_base(p_img, p_out):
    '''调整base图的大小使得长宽比为2:1
    '''
    (a, b) = p_img.size
    x=0; y=0; w=0; h=0
    if a / b < 2:    # based on the width
        w = a
        h = a / 2
        x = 0
        y = b - h
    elif a / b >= 2:    # based on the height
        w = 2 * b
        h = b
        x = (a - w) / 2
        y = 0
    region = p_img.crop((x, y, x+w, y+h))
    region.save(p_out)
    return Image.open(p_out)

def mark_qrcode(p_base, p_qr, p_out_file, p_w, p_h):
    ''' 将二维码粘贴在cover图上
    '''
    p_base.paste(p_qr, (p_w, p_h))
    p_base.save(p_out_file)
    print "[*] Combined..."


def mkdir_if_not_exist(p_l_path):
    if isinstance(p_l_path, list):
        for i in p_l_path:
            if os.path.isdir(i):
                shutil.rmtree(i)
            os.makedirs(i)
    else:
        print "[!] Please insert a list"

def write_to_zip(p_num=1):
    '''将图片打包到zip压缩文件
    '''
    t = time.strftime("%Y%m%d", time.localtime())
    n = u'图片' + t + '.zip'
    print "[*] Starting zipping..."
    with zipfile.ZipFile(n, 'w') as myzip:
        for i in range(0,p_num):
            myzip.write(FILE_COMB.format(i))
    print "[*] Zipped!"
    return n

def demo():
    r0 = _s.get(URL_API)
    data = json.loads(r0.content, object_hook=JSONObject)
    for i in data.data:
        print "[" + i.title + "]"                 # 标题
        print_()
        print i.date                              # 发布时间
        print "    " + i.desc                     # 描述
        print i.cover                             # 封面图url
        print URL_ARTICLE_PRE.format(i.id)        # 带文章id的完整文章url


def main():
    mkdir_if_not_exist([DIR_BASE, DIR_BASE_re, DIR_QR, DIR_QR_THUMB, DIR_COMB])    # 新建目录，存放图片
    r = _s.get(URL_API)                                              # 获取所有所需的json信息
    data = json.loads(r.content, object_hook=JSONObject)
    name_pic  = ""                                                   # 图片名字
    url_cover = ""                                                   # 封面图名字
    url_paper = ""                                                   # paper的url
    name_paper= ""                                                   # 文章名字(标题)
    for i in data.data:
        name_paper = i.title                                         # 先得到文章的名字
        name_pic   = name_paper                                      # 将图片名字设置为文章的标题
        url_cover  = i.cover
        fetch_img_and_save(_s, url_cover, FILE_BASE.format(name_pic))
        url_qr  = URL_QR_API + URL_ARTICLE_PRE.format(i.id)          # 待给二维码网站的url
        print_()
        log(name_pic)
        log(url_qr)
        fetch_img_and_save(_s, url_qr, FILE_QR.format(name_pic))
        
        img_qr   = Image.open(FILE_QR.format(name_pic))
        img_qr_thumb = resize_qr(img_qr, 3, 3, FILE_QR_THUMB.format(name_pic))  # 300*300 -> 100*100
        img_base = Image.open(FILE_BASE.format(name_pic))
        img_base_re = resize_base(img_base, FILE_BASE_RE.format(name_pic))    #将ima_base这个Image转换成合乎base大小的图，然后保存到文件
        ### 得到这两个图片的长宽大小
        base_re_w, base_re_h         = img_base_re.size
        qr_thumb_w, qr_thumb_h       = img_qr_thumb.size
        ### 给base图添打上二维码
        mark_qrcode(img_base_re, img_qr_thumb, FILE_COMB.format(name_pic), base_re_w-qr_thumb_w, base_re_h-qr_thumb_h)
    #write_to_zip()

if '__main__' == __name__:
    if IS_DEMO:  demo()
    main()


