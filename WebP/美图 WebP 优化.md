`## 美图图像业务优化

[TOC]

### 背景

&emsp;&emsp;近些年来，由于网络技术和互联网的普及，人们愈发习惯通过图片分享自己的生活，图片的流量也一直以指数级增长，带来的流量压力也愈发增大，因此业界许多优秀的互联网公司都开始着力于保证图像质量的前提下缩小图像体积。	

&emsp;&emsp;美图公司是一家以图像、视频服务为主的移动互联网公司，广为用户熟知的是以美图秀秀，美颜相机，美拍为核心的应用矩阵，目前也正式上线了电商应用美铺和社交应用闪聊，或多或少都涉及图像服务，[图像格式](https://en.wikipedia.org/wiki/Comparison_of_graphics_file_formats)也基本都是 JPEG 和 PNG，熟悉图像编解码领域的同学都知道，JPEG 是一种有损压缩格式且不支持阿尔法透明通道，PNG 则是无损的，前者是目前互联网最流行的图像格式，能够将原图大比例压缩，节省很大的带宽，后者则是以高清图像，能够将图像高质量的展示出来，但是成本很高，不适合重图像业务。因此，如果能够在保证用户视觉体验的前提下，实现更高的压缩比，带来的流量节省将是很客观的，这篇文章将会介绍美图在图像编解码应用的探索过程中积累的经验。



### 调研

#### Guetzli

&emsp;&emsp;首先，我们把目光看向了 Google 今年 4 月份开源了一种新的 JPEG 编码算法 - [Guetzli](https://github.com/google/guetzli)，它编码得到的 JPEG 图像比 libjpeg 产生的同等质量的图像小 20%-30%，之所以优先研究 JPEG 编码算法，是因为 JPEG 的兼容性很广，业务能够以极低的成本接入使用。

&emsp;&emsp;我们知道，传统的 libjpeg 库已经能将原图压缩到很低，如何将流行30年的算法改进如此之大，最开始显然是不信的，但考虑到 Google 在图像编解码领域的权威，我们还是带着极大的好奇心开始了对 Guetzli 的研究，从论文介绍的原理上来看，Guetzli 算法引入了一种评价图像之间质量差异的标准-[Butteraugli](https://github.com/google/butteraugli)，在算法编码过程中使用其来计算编码后产生的图像和原图的质量差异，即失真度，从而决定后续的编码策略，通过这样一个编码-评分-反馈的逻辑，实现在保证图像质量前提下，尽可能对原图进行压缩。

&emsp;&emsp;可想而知，该算法的编码时间将会是传统的 libjpeg 算法的数倍，并且作者提到该算法运行时需要较高的内存，换算公式是 1M像素=300MB 内存，例如 1000*1000 像素的图像编码需要 300MB 内存，也就是牺牲编码时间和内存换取跟大的压缩比，这对于对编码时间要求比较苛刻的服务显然是不实用的，但是考虑到这只是初始版本，还有一定的成长空间，虽然作者短期并不打算优化内存使用，最重要的是我们有些服务对编码时间并不关心，例如开屏广告，这种图像一般 Size 较大，对图像质量的要求也很高。因此，虽然现在 Guetzli 并不适合大规模应用，但还是值得持续关注的。



#### WebP

&emsp;&emsp;源于视频编码领域 [VP8](https://zh.wikipedia.org/wiki/VP8) 的  [WebP](https://developers.google.com/speed/webp/)  是 Google 2010年开源出来的图像编解码算法， 并且持续受到重视，本身支持图像的有损压缩和无损压缩，也支持类似 GIF 的动图格式，据官方说明，WebP 的无损压缩格式比 PNG 少 26% 的图片体积，有损压缩格式比同等质量下的 JPEG 图片少 25%-34%，值得一提的是，WebP 的无损格式支持透明度（即阿尔法透明通道），对于 RGB 的图像，其有损压缩格式亦支持透明度。

&emsp;&emsp;对比其他第三方资料，官方数据似乎有一些谦虚，例如腾讯 ISUX 有提到 “无损压缩后的 WebP 比 PNG 文件少了 45％ 的文件大小，即使这些 PNG 文件经过其他压缩工具压缩之后，WebP 还是可以减少 28％ 的文件大小。” 和 “YouTube 的视频略缩图采用 WebP 格式后，网页加载速度提升了 10%；谷歌的 Chrome 网上应用商店采用 WebP 格式图片后，每天可以节省几 TB 的带宽，页面平均加载时间大约减少 1/3；Google+ 移动应用采用 WebP 图片格式后，每天节省了 50TB 数据存储空间。”，对于一个数据如此优秀的编码算法，我们当然要对它进行跟深的窥视了。

##### 有损压缩原理

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![WebP 编码原理](http://ww4.sinaimg.cn/large/006tNbRwgy1fflvuah36sj30ko0i8acq.jpg)

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 0: WebP 有损压缩流程图**

&emsp;&emsp;WebP 的编码步骤基本类似于 JPEG 编码，主要包含格式转换、分割子块、预测编码、FDCT、量化、Z排列、熵编码等，其中预测编码是源自 VP8 的帧内预测模型，也是 WebP 较 JPEG 改进如此之大的主要原因，由于篇幅限制，这里我们只对该过程进行进一步的说明。

&emsp;&emsp;在介绍 VP8 帧内预测模型之前，我们首先要知道其使用的格式 YUV，这是三种分量，Y 表示亮度分量，UV 表示色度分量，由于人眼对亮度的敏感度明显强于色度，所以在编码之前，如果图像是 RGB 模式，需要转换成 YUV 格式，通过减少色度数据存储，可以有效减少占用的空间并且不会对视觉效果造成大的影响；

帧内预测模型使用三种类型的宏块（macroblocks），4x4 亮度块，16x16 亮度块和 8x8 色度块，基于之前编码好的宏块，预测多余的动作和颜色信息，预测的模型主要有 4 种：

```
	1. H_PRED(Horizontal-水平预测)：使用 Block 左边的一列 Left 来填充 Block 中的每一列;

	2. V_PRED(Vertical-垂直预测)：使用 Block 上边的一行 Above 来填充 Block 中的每一行;

	3. DC_PRED(Average-均值预测)：使用 Left 和 Above 中所有像素的平均值作为唯一的值填充 Block;

	4. TM_PRED(TrueMotion-运动预测)：使用渐进的方式，记录上面一行的渐进差，以同样的差值，以 Left 为基准拓展每一行。

```


&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![帧内预测模型](http://ww2.sinaimg.cn/large/006tNbRwgy1fflvu4u5ypj30py0gidhx.jpg)

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 1: 帧内预测模型**

&emsp;&emsp;除了三种宏块通用的四种模型之外，对于 4x4 的亮度块，还有额外的 6 种近似于水平和垂直预测的模型，可以在示意图中找到。

&emsp;&emsp;据[官方介绍](https://developers.google.com/speed/webp/docs/compression)，WebP 有损压缩优于JPEG 算法的原因主要有三点，除了上面介绍的预测编码之外，自适应分块策略通过将图像划分为若干（默认是 4 ）个视觉效果相近的区域，每个区域根据其特性个性化设置压缩参数（例如量化步长）；最后相对于 JPEG 采用的哈夫曼编码，WebP 的布尔算术编码也带来了额外 5%-10% 的压缩比。

##### 业务应用和兼容性

&emsp;&emsp;在业务普及上，Google 的 [Youtube](https://www.google.com/events/io/io14videos)、Gmail、Google Play 等产品都已经应用了 WebP 格式，其应用商店也早已经完全使用了 WebP，除此之外，国外如 Facebook，ebay等巨头，国内如淘宝，腾讯等一线公司都已经在使用 WebP 作为新的图像格式。

&emsp;&emsp;兼容性上，对于目前据统计目前全球约有 73.35%， 国内约 60.67% 的用户可以直接体验 WebP，除了本家兄弟 Chrome（23+） 和 Android （4.0+）支持 WebP 之外，QQ 和 UC 等基于 Chromium 内核的浏览器也支持，并且对于移动端，除了 Android 4.0 以上版本对 WebP 的原生支持以外，其他版本和 iOS 也可以通过官方提供的解析库支持 WebP：[Android](https://github.com/alexey-pelykh/webp-android-backport) 和 [iOS](https://github.com/carsonmcdonald/WebP-iOS-example)，并且 Safari 和 Firefox 也都有支持的 WebP 的计划，对于动态 WebP，目前 Chrome 32+ 和 Opera 19+已经有支持，详细数据请参考：[兼容性神器](http://caniuse.com/#search=webp)。
![](https://ws4.sinaimg.cn/large/006tKfTcly1ffvaayy883j31kw0sb47h.jpg)



### 对比测试

&emsp;&emsp;通过上述的调研，我们最后选取了 WebP 作为图像业务优化的候选项，并通过一系列测试和现有的 JPEG 编码器做对比。对于传统的 JPEG 编码实现，主要包括 Libjpeg-turbo 和 Mozjpeg，其中 Libjpeg-turbo 是经典 Libjpeg 的复刻，采用[单指令流多数据流](https://zh.wikipedia.org/wiki/%E5%8D%95%E6%8C%87%E4%BB%A4%E6%B5%81%E5%A4%9A%E6%95%B0%E6%8D%AE%E6%B5%81)（SIMD）[指令](https://zh.wikipedia.org/wiki/%E6%8C%87%E4%BB%A4%E9%9B%86%E6%9E%B6%E6%A7%8B)来加速JPEG编码和解码基础效率，也就是优化传统算法的编解码速度，目前许多地方使用的 Libjpeg 大多是指 Libjpeg-turbo，Mozjpeg 则是 Libjpeg-turbo 的复刻，旨在通过减少文件大小（约10%）来加快网页的加载时间，以及在不改变图像质量的前提下提高编码效率，因此这里对比将会同时考虑这两种编码器（libjpeg-turbo version 1.5.1, mozjpeg version 3.1）； WebP 使用的则是 libwebp-0.6.0。

&emsp;&emsp;为了衡量不同编码器的压缩效果，我们采用 [SSIM]()（[结构相似性](https://zh.wikipedia.org/wiki/%E7%B5%90%E6%A7%8B%E7%9B%B8%E4%BC%BC%E6%80%A7)）作为质量指标，数值介于 0-1 之间，压缩后图像质量越高，和原图的 SSIM 越接近于 1，可以用来表示图像压缩前后的相似度／失真度，这是一种公认的比 SNR 更好的质量标准。需要说明的是，Guetzli 使用的 Butteraugli 指标是基于人眼对图像的视觉效果的一种度量器，本身是一种很符合肉眼的一种标准，但是由于该指标的正确性和成熟度有待论证，所以这里也就没有选择其作为衡量质量的手段。

&emsp;&emsp;我们从压缩比，压缩时间，压缩质量三个维度对比这三种编码器，为了尽可能接近线上真实需求，测试场景为电商服务（随机抓取 100 张 JPEG 图像）和广告服务（随机抓取 50 张 JPEG 图像），测试环境为 macOS Sierra V10.12，2.5 GHz Intel Core i7 处理器，内存为 16 GB 1600 MHz DDR3。

#### 测试一：BPP-SSIM

**测试方法：**
```

	1. 利用三种编码器分别将 JPEG 原图在所有可选 Quality 参数下压缩，记录图像 BPP (bits per pixel) 和 SSIM 数值，其中 Mozjpeg 和 Libjpeg-turbo 均加上参数 “-optimize”，其余使用默认值，WebP 除 “-q” 外，其余使用默认值；
	2. 根据 BPP 和 SSIM 的对应关系绘图。
```


##### 电商服务

电商图片集合按照大小一分为二，分开对比，以考量不同图像大小对编码器编码性能的影响：

###### AVG File Size=803.38KB


&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![BPP-SSIM](http://ww3.sinaimg.cn/large/006tNbRwly1ffod8kia7pj30sg0h2wgt.jpg)

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 2: BPP-SSIM**

###### AVG File Size=72.27KB


&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![](http://ww2.sinaimg.cn/large/006tNbRwly1ffomtmejl7j30sg0h3tau.jpg)

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 3: BPP-SSIM**

##### 广告服务

###### AVG File Size=322.49KB


&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![BPP-SSIM](http://ww4.sinaimg.cn/large/006tNbRwly1ffob5ijlf4j30sg0h240q.jpg)

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 4: BPP-SSIM**



#### 测试二：Quality-Size

**测试方法：**

```
1. 利用 WebP 将 JPEG 原图在不同 Quality 参数下压缩，记录图像体积大小和 SSIM 数值；
2. 分别利用 MozJPEG 和 Turbo 将图像压缩到与步骤一中 SSIM 数值尽可能接近，记录图像体积大小。
注：参数同测试一。
```

**WebP-Quality = 65, WebP vs MozJPEG vs Turbo**

|                                          | **电商**(AVG: 803.38KB) | **电商**(AVG: 72.27KB) | **广告**(AVG: 322.49KB) |
| :--------------------------------------- | --------------------- | -------------------- | --------------------- |
| **WebP: Average File Size** **(Average SSIM)** | 134.10KB (0.9453)     | 19.37KB (0.9619)     | 52.86KB (0.9393)      |
| **Mozjpeg: Average File Size** **(Average SSIM)** | 155.13KB (0.9464)     | 26.86KB (0.9624)     | 71.23KB (0.9401)      |
| **WebP/MozJPEG**                         | 0.86                  | 0.72                 | 0.74                  |
| **Turbo: Average File Size** **(Average SSIM)** | 184.41KB (0.9463)     | 35.06KB (0.9626)     | 94.03KB (0.9406)      |
| **WebP/Turbo**                           | 0.73                  | 0.55                 | 0.56                  |

 **WebP-Quality = 75, WebP vs MozJPEG vs Turbo**

|                                          | **电商**(AVG: 803.38KB) | **电商**(AVG: 72.27KB) | **广告**(AVG: 322.49KB) |
| :--------------------------------------- | --------------------- | -------------------- | --------------------- |
| **WebP: Average File Size** **(Average SSIM)** | 153.17KB (0.9522)     | 22.12KB (0.9665)     | 58.77KB (0.9427)      |
| **Mozjpeg: Average File Size** **(Average SSIM)** | 174.69KB (0.9533)     | 29.84KB (0.9676)     | 78KB (0.9433)         |
| **WebP/MozJPEG**                         | 0.88                  | 0.74                 | 0.75                  |
| **Turbo: Average File Size** **(Average SSIM)** | 203.96KB (0.9531)     | 38.81KB (0.9677)     | 101.8KB (0.9435)      |
| **WebP/Turbo**                           | 0.75                  | 0.57                 | 0.58                  |

**WebP-Quality = 85, WebP vs MozJPEG vs Turbo**

|                                          | **电商**(AVG: 803.38KB) | **电商**(AVG: 72.27KB) | **广告**(AVG: 322.49KB) |
| :--------------------------------------- | --------------------- | -------------------- | --------------------- |
| **WebP: Average File Size** **(Average SSIM)** | 239.40KB (0.9707)     | 34.43KB (0.97776)    | 85.83KB (0.9529)      |
| **Mozjpeg: Average File Size** **(Average SSIM)** | 252.74KB (0.9723)     | 38.44KB (0.9785)     | 106.66KB (0.9537)     |
| **WebP/MozJPEG**                         | 0.95                  | 0.90                 | 0.81                  |
| **Turbo: Average File Size** **(Average SSIM)** | 290.91KB (0.9716)     | 48.47KB (0.9783)     | 133.51KB (0.9536)     |
| **WebP/Turbo**                           | 0.82                  | 0.71                 | 0.65                  |



#### 测试三：编码时间

测试方法同上，记录图像体积大小改为记录编码时间。

**WebP-Quality = 75, WebP vs MozJPEG vs Turbo**

|                                          | **电商**(AVG: 803.38KB) | **电商**(AVG: 72.27KB) | **广告**(AVG: 322.49KB) |
| :--------------------------------------- | --------------------- | -------------------- | --------------------- |
| **WebP: Average Time** **(Average SSIM)** | 0.2821 (0.9522)       | 0.0744s (0.9665)     | 0.1717s  (0.9427)     |
| **Mozjpeg: Average Time** **(Average SSIM)** | 0.2627s (0.9533)      | 0.0656s (0.9676)     | 0.1529s  (0.9433)     |
| **WebP/MozJPEG**                         | 1.07                  | 1.13                 | 1.12                  |
| **Turbo: Average Time** **(Average SSIM)** | 0.0170s (0.9531)      | 0.0077s (0.9677)     | 0.0126s (0.9435)      |
| **WebP/Turbo**                           | 16.59                 | 9.66                 | 13.63                 |

#### 测试四：Guetzli

&emsp;&emsp;Guetzli 是为高质量图像量身定做的 JPEG 编码算法，虽然同时支持 PNG 和 JPEG 的压缩，但是官方也明确提到，在有损压缩后的图像上，算法表现比较差，所以不太适合大多数业务场景。那么在  PNG 的高清图像上，Guetzli 算法的性能又如何呢？为此，我们额外测试了在 Lena(PNG, 512x512, 501KB) 图像上四种编码器的性能表现：
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![](http://ww1.sinaimg.cn/large/006tNc79ly1ffpd0avdyxj30sg0h2di4.jpg)
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 5: BPP-SSIM**

&emsp;&emsp;Guetzli 支持的质量参数范围是 84-110 ，所以可选的参数值较少。根据上图可以发现，Guetzli 在图像质量要求很高的场景下优势很大，可以很好的降低失真度。
##### 编码时间

 **WebP-Quality = 75, WebP vs Guetzli**

|                                          | **Lena**(512.67KB) |
| :--------------------------------------- | ------------------ |
| **WebP: Average Time** **(Average SSIM)** | 0.0446s (0.8570)   |
| **Guetzli: Average Time** **(Average SSIM)** | 24.6079s (0.8765)  |
| **Guetzli/WebP**                         | 551.7              |

&emsp;&emsp;在编码时间上，Guetzli 的劣势很明显，这也说明了其现阶段不适合在常见业务场景下大规模应用。


### 指导和建议

&emsp;&emsp;综合对比压缩性能和质量的数据，可以发现实际应用上 WebP > Mozjpeg > Libjpeg-Turbo ，利用 WebP 格式存储图像，各业务带来的收益为 20% 以上，考虑到美图整体的图像业务总量，这已经是一个不错的的改进，那么，如何设置 WebP 的压缩参数以及 WebP 又有哪些需要注意的点呢，我们继续对 WebP 的应用细节做了探究。

#### WebP 最佳参数

&emsp;&emsp;WebP 虽然支持动图，有损／无损压缩，我们主要探究的还是其有损压缩场景，我们知道，WebP 支持的质量参数范围是 0-100，为了得到有损压缩最佳配置，我们对 500 张电商图像使用不同的压缩配置，得到了相应的测试数据：


&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![](http://ww2.sinaimg.cn/large/006tNbRwly1ffomozntjfj30sg0ozdio.jpg)			          

&emsp;&emsp;综合来看，"-q=75" 时，图片质量和体积以及压缩时间达到了很好的平衡， 从上图中可以看到大于 75 之后压缩比下降速率和编码时间上升速率明显加快，而且约 96% 的图像在 75 可以达到一个可靠的图像质量，因此在电商场景下，我们推荐使用 75 为有损压缩质量参数，至于其他的场景，据测试，75 也是一个很好的选择，这里就不再展示。

&emsp;&emsp;此外，WebP 还支持参数 "-m" 以改进图像压缩体积，默认值是 4，支持 0-6 的配置，类似于 Libjpeg 的参数 “-optimize” ，都是通过增加编码耗时换取更小的体积，我们发现，在 “-q 75” 参数下，加上 "-m 6" 之后，WebP 图像体积进一步减少 7.6%，耗时增加约 80%。

#### 色差

在我们实际应用 WebP 过程中，发现在某些 JPEG 图像转 WebP 格式之后，会有一些较为明显的色差，例如 Figure-11：


&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![JPEG](http://ww2.sinaimg.cn/large/006tNbRwgy1ffombnthvvj3040074mxa.jpg)&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![WebP](http://ww4.sinaimg.cn/large/006tNbRwly1ffomk2w1luj303z0743yp.jpg)&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;![WebP](http://ww4.sinaimg.cn/large/006tNbRwgy1ffomlxzvh3j3040074weo.jpg)


&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 10: JPEG 原图**&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 11: WebP  编码图像**&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 12: WebP 参数调整后图像** 


&emsp;&emsp;可以发现，Figure-11 的颜色相对 Figure-10 变红变暗了，跟进这个问题之后，发现是因为 JPEG 采用的色彩格式是 YUVJ420P，对应的色彩区间是 0-255，而 WebP 采用的色彩格式是 YUV420P，对应的色彩区间是 16-235，也就是说如果单纯的转码，会丢失 0-15，236-255 的色彩，也就是出现了色差。虽然从产品角度来看，这样的色差是可以容忍的，但是从技术角度，我们当然是希望可以有解决色差的方法，进一步跟进发现，cwebp 提供了一个 “-metadata” 的参数，可以将原图的额外信息复制到 WebP 图像上，虽然会增加额外的存储空间，但是可以保证视觉体验与原图一致，并且增加的空间也仅限于保存原图的额外信息那一部分。通过增加 "-metadata all", 转码后的 WebP 图像消去了色差，可以参看 Figure-12：

&emsp;&emsp;该参数有 “all, none, exif, icc, xmp” 五种可选项，默认是 none，支持 exif, icc, xmp 三种类型或其任意组合的信息保留， 例如，上述 JPEG 原图额外信息正是 [ICC Profile](https://en.wikipedia.org/wiki/ICC_profile) 信息，可以使用 "-metadata icc" 或者 "-metadata all" 保证转码质量。

#### SSIM 的缺陷

&emsp;&emsp;在通过测试寻找 WebP 的最佳压缩质量参数的过程中，我们发现，某些图像使用 "-q 10" 压缩后， SSIM 的值表现依旧很优秀（>0.98），但是其实压缩后的图已经明显失真，这个问题让我们措手不及，因为整个对比对 SSIM 的依赖程度很高，如果质量评分工具不可靠，那么整体的测试也就不可靠，经过对这部分测试图像分析发现，它们有一个共同的特征就是图像纯色区域占据整幅图像的比例很高，失真度较高的往往是除了纯色区域之外的复杂区域，参看下图。因此，对于这种类型的图像，我们需要使用更高的参数来保证编码质量，不能简单地使用 SSIM 来衡量编码后的质量。


![JPEG 原图](http://ww4.sinaimg.cn/large/006tNbRwgy1ffonsla0obj30ds07r0so.jpg)![WebP(-q 10 dssim 0.0024)](http://ww1.sinaimg.cn/large/006tNbRwgy1ffonu13t80j30ds07qt8p.jpg)
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 13: JPEG 原图**&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Figure 14: WebP(-q 10 ssim 0.98) 图像**



### 其他

**质量评测工具：**

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**SSIM:** http://mehdi.rabah.free.fr/SSIM/SSIM.cpp 

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**DSSIM:** https://github.com/pornel/dssim/ 

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Butteraugi:** https://github.com/google/butteraugli



**WebP 落地相关：**

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**Android 4.0 以下:** https://github.com/alexey-pelykh/webp-android-backport 

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**iOS:** https://github.com/carsonmcdonald/WebP-iOS-example 

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**JS 插件:** http://webpjs.appspot.com/ 

**解码测试对比：** https://isux.tencent.com/introduction-of-webp.html

**WebP 效果体验（可供产品同学对比使用）：** http://zhitu.tencent.com/ 

**WebP Issue 社区：** https://bugs.chromium.org/p/webp/issues/list

### 参考文献

https://developers.google.com/speed/webp/ 

https://zhuanlan.zhihu.com/p/23648251

https://research.googleblog.com/2017/03/announcing-guetzli-new-open-source-jpeg.html`