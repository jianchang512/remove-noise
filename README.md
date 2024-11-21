## 音频降噪小工具

本工具利用通义实验室的 [ZipEnhancer模型](https://modelscope.cn/models/iic/speech_zipenhancer_ans_multiloss_16k_base)) 实现音频降噪功能，提供便捷的Web UI界面和API接口。

在语音识别转录、语音克隆等应用中，音频噪声会显著影响处理精度。因此，对原始音视频进行预处理降噪至关重要。ZipEnhancer 模型安装简便，且降噪效果良好，故此开发本小工具以方便使用。

> ZipEnhancer模型原理:
>
> 本工具所使用的 [ZipEnhancer模型](https://modelscope.cn/models/iic/speech_zipenhancer_ans_multiloss_16k_base)  正是基于深度学习的语音增强模型。
>
>它采用了一种改进的Transformer网络结构，并结合了多任务学习策略，可以同时进行语音降噪、语音增强和声学回声消除。
>
>该模型通过大量的语音数据进行训练，学习到了噪声和语音信号之间的复杂映射关系，能够有效地去除各种类型的噪声，并提升语音质量。
>
> 其核心思想是利用自注意力机制捕捉语音信号的长时相关性，并通过多头注意力机制从不同角度提取语音特征，从而实现更精细的噪声抑制和语音增强。


## 使用方法

**预打包版本:**

1. 下载Win预打包版本并解压 (https://github.com/jianchang512/remove-noise/releases/download/v0.1/win-remove-noise-0.1.7z) 。
2. 双击`runapi.bat`文件，系统将自动打开浏览器，访问地址为`http://127.0.0.1:5080`。
3. 选择需要处理的音频或视频文件即可开始降噪。


**源码部署:**

1. **环境准备:**  确保已安装Python 3.10至3.12版本。
2. **安装依赖:**  执行以下命令安装必要的Python包：

   ```bash
   pip install -r requirements.txt --no-deps
   ```

3. **CUDA支持 (可选):**  如果您需要使用CUDA 12.x加速处理，请先卸载旧版本的PyTorch相关包，再安装CUDA 12.1兼容版本：

   ```bash
   pip uninstall -y torch torchaudio torchvision
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

4. **运行程序:**  安装完成后，执行以下命令启动服务：

   ```bash
   python api.py
   ```
> 1. Linux系统需安装 libsndfile库，`sudo apt-get update`,`sudo apt-get install libsndfile1`
> 
> 2. 一个小坑，安装后请确保使用的 `datasets`版本为 3.0，否则降噪处理时 modelscope 可能报各种错误. `pip list|grep datasets`


## 界面预览

![界面预览](./static/1.jpg)


## API使用方法

本工具提供RESTful API接口，方便集成到其他应用中。

**接口地址:** `http://127.0.0.1:5080/api`

**请求方法:** POST

**请求参数:**

* `stream`:  整数类型，控制返回结果格式。
    * `0`: 返回降噪后音频的URL地址。
    * `1`: 直接返回降噪后的WAV音频数据。
* `audio`:  二进制文件类型，待处理的原始音频或视频文件。


**返回结果 (JSON格式):**

* **成功:**
    * `stream=0`:  `{ "code": 0, "data": { "url": "音频URL地址" } }`
    * `stream=1`:  返回降噪后的WAV音频数据 (二进制数据)。
* **失败:**  `{ "code": -1, "msg": "错误信息" }`


**示例代码 (Python):**

```python
import requests

# stream=0: 获取音频URL
res = requests.post('http://127.0.0.1:5080/api', data={"stream": 0}, files={"audio": open('./300.wav', 'rb')})

if res.status_code != 200:
    print(f"请求失败: {res.text}")
    exit(1)  # 使用 exit(1) 表示非零退出码，指示错误发生

print(f"降噪后音频URL: {res.json()['data']['url']}")


# stream=1: 获取WAV数据
res = requests.post('http://127.0.0.1:5080/api', data={"stream": 1}, files={"audio": open('./300.wav', 'rb')})

if res.status_code != 200:
    print(f"请求失败: {res.text}")
    exit(1)

with open("ceshi.wav", 'wb') as f:
    f.write(res.content)
print("降噪后的音频已保存为 ceshi.wav")
```


