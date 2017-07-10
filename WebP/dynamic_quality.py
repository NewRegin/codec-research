#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import cStringIO
import PIL.Image
import os
import re
import time
from math import log
from ssim import compute_ssim
 
def get_ssim_at_quality(photo, quality):
    """Return the ssim for this WebP image saved at the specified quality"""
    ssim_photo = cStringIO.StringIO()
    # optimize is omitted here as it doesn't affect
    # quality but requires additional memory and cpu
    photo.save(ssim_photo, format="WebP", quality=quality)
    ssim_photo.seek(0)
    ssim_score = compute_ssim(photo, PIL.Image.open(ssim_photo))
    return ssim_score
 
 
def _ssim_iteration_count(lo, hi):
    """Return the depth of the binary search tree for this range"""
    if lo >= hi:
        return 0
    else:
        return int(log(hi - lo, 2)) + 1
 
def webp_dynamic_quality(original_photo):
    """Return an integer representing the quality that this WebP image should be
    saved at to attain the quality threshold specified for this photo class.
 
    Args:
        original_photo - a prepared PIL WebP image 
    """
    ssim_goal = 0.98
    # q 选择的最大值
    hi = 75
    # q 选择的最小值
    lo = 60
 
    # working on a smaller size image doesn't give worse results but is faster
    # changing this value requires updating the calculated thresholds
    photo = original_photo.resize((400, 400))
 
    # 95 is the highest useful value for WebP. Higher values cause different behavior
    # Used to establish the image's intrinsic ssim without encoder artifacts
    normalized_ssim = get_ssim_at_quality(photo, 95)
    selected_quality = selected_ssim = None
    lowest_ssim = get_ssim_at_quality(photo, lo)
    if (lowest_ssim/normalized_ssim) >= ssim_goal:
        return lo, lowest_ssim
    # loop bisection. ssim function increases monotonically so this will converge
    for i in xrange(_ssim_iteration_count(lo, hi)):
        curr_quality = (lo + hi) // 2
        curr_ssim = get_ssim_at_quality(photo, curr_quality)
        ssim_ratio = curr_ssim / normalized_ssim
 
        if ssim_ratio >= ssim_goal:
            # continue to check whether a lower quality level also exceeds the goal
            selected_quality = curr_quality
            selected_ssim = curr_ssim
            hi = curr_quality
        else:
            lo = curr_quality
 
    if selected_quality:
        return selected_quality, selected_ssim
    else:
        default_ssim = get_ssim_at_quality(photo, hi)
        return hi, default_ssim

def output_image(image, quality, photo):
        photo.save(image+"-"+str(this_quality)+".webp", format="WebP", quality=quality)

# 解析路径参数，可以是文件夹也可以是文件
def list_images(rootDir):
    images = []
    if os.path.isdir(rootDir):
        for files in os.walk(rootDir):
            for file in files[2]:
                if re.match("^(?!.*test).*\.jpg$|^(?!.*test).*\.png$", file, flags=0) != None:
                    images.append(os.path.join(files[0],file))
    elif os.path.isfile(rootDir):
        if re.match("^(?!.*test).*\.jpg$|^(?!.*test).*\.png$", rootDir, flags=0) != None:
            images.append(rootDir)
    return images

description = '\n'.join([
        'Compares encode algs using the SSIM metric.',
        '  Example:',
        '   python dynamic_quality.py  --path ./images/JPG/'
    ])

parser = argparse.ArgumentParser(
    prog='compare', formatter_class=argparse.RawTextHelpFormatter,
    description=description)
parser.add_argument('--path', default='./samples/', help='images path JPG/PNG')
parser.add_argument("--out", type=int, default=0, help="output the webp: 0 is no, 1 is yes")

args = parser.parse_args()
images = list_images(args.path)
image_quality = {}

start = time.time()
for image in images:
    img = PIL.Image.open(image)
    this_quality, this_ssim = webp_dynamic_quality(img)
    # print (image)
    print (this_quality, this_ssim)
    image_quality[image] = this_quality

    if args.out == 1:
       output_image(image, this_quality, img) 

print "total time(s):"
print(time.time()-start)
