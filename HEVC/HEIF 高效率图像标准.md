## HEIF 高效率图像格式

[TOC]

### 优势&劣势

#### 优势

1. 相同客观质量下的 JPEG 的大小是 HEIF 的 2.39 倍；
2. 支持 metadata（Exif, XMP, MPEG-7），ICC 色彩格式，非破坏性编辑，缩略图，图像序列（例如 iphone 的 live photo）等；
3. 苹果在 iOS 11 和 High Sierra 支持 HEIF；
4. […](https://zh.wikipedia.org/wiki/%E9%AB%98%E6%95%88%E7%8E%87%E5%9B%BE%E5%83%8F%E6%96%87%E4%BB%B6%E6%A0%BC%E5%BC%8F#.E7.89.B9.E6.80.A7.E6.AF.94.E8.BE.83)

#### 劣势

1. 昂贵的专利费，限制了硬件和付费软件的普遍应用。

### 安装&测试

[Convert2HEIF](http://jpgtoheif.com/)

注意：

​	原图需要的长和宽是色度采样的整数倍，例如 1024 可以，1023 不可以。

### 原理

[HEIF 白皮书](https://github.com/NewRegin/codec-research/blob/master/HEVC/heif%20%E7%99%BD%E7%9A%AE%E4%B9%A6.docx)

### 参考资料

1. Wiki: https://en.wikipedia.org/wiki/High_Efficiency_Image_File_Format
2. Github 源代码（C++&JS API）：https://github.com/nokiatech/heif
3. Nokia HEIF 官网：https://nokiatech.github.io/heif/index.html
4. JPG2HEIF：http://jpgtoheif.com/

