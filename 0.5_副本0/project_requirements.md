# 中文姓名生成与语音朗读功能项目需求文档

## 1. 项目概述
本项目旨在为外国用户提供中文姓名生成服务，包含多姓名选项展示、古风卡片式布局以及姓名发音朗读功能。

## 2. 功能需求
### 2.1 多姓名生成功能
- 每次请求生成3-5个中文姓名选项
- 每个姓名包含汉字、拼音及详细解释
- 姓名需符合中国传统文化美学

### 2.2 古风卡片式展示
- 采用中国风UI设计，包含传统纹样边框
- 卡片背景使用宣纸纹理效果
- 字体选用具有书法感的中文字体
- 卡片布局支持响应式设计

### 2.3 文本转语音功能
- 为每个姓名添加语音朗读按钮
- 使用喇叭图标作为播放按钮
- 点击后播放姓名的标准普通话发音
- 支持播放状态显示

## 3. 技术实现方案
### 3.1 后端实现
#### 3.1.1 姓名生成接口改进
- 修改`/generate-name`接口，使其返回多个姓名选项
- 优化提示词工程，确保生成姓名的多样性和文化适宜性

#### 3.1.2 文本转语音接口开发
- 新增`/generate-speech`接口
- 集成Silicon Flow API的文本转语音服务
- 使用模型：`FunAudioLLM/CosyVoice2-0.5B`
- 支持语音文件生成与存储

### 3.2 前端实现
#### 3.2.1 古风卡片组件
- 创建可复用的姓名卡片组件
- 添加中国传统元素的CSS样式
- 实现卡片悬停动画效果

#### 3.2.2 音频播放功能
- 开发音频播放控制组件
- 实现播放/暂停状态管理
- 添加音频加载状态提示

## 4. 实施步骤
### 4.1 第一阶段：后端开发
1. 修改姓名生成接口，支持多结果返回
2. 开发文本转语音接口
3. 实现语音文件存储功能

### 4.2 第二阶段：前端开发
1. 创建古风卡片UI组件
2. 实现多卡片布局
3. 开发音频播放功能
4. 整合前后端交互

### 4.3 第三阶段：测试与优化
1. 测试姓名生成质量
2. 验证语音朗读准确性
3. 优化UI/UX体验
4. 性能测试与优化

## 5. API集成详情
### 5.1 文本转语音API调用示例
```python
import requests
import os

def generate_speech(text, voice="FunAudioLLM/CosyVoice2-0.5B:alex"):
    url = "https://api.siliconflow.cn/v1/audio/speech"
    payload = {
        "model": "FunAudioLLM/CosyVoice2-0.5B",
        "input": text,
        "voice": voice,
        "response_format": "mp3",
        "sample_rate": 32000,
        "speed": 1,
        "gain": 0
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('SILICON_FLOW_API_KEY')}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.content
```

## 6. 资源需求
- Silicon Flow API密钥
- 中文字体资源（建议使用"思源宋体"或"方正清刻本悦宋简体"）
- 中国传统纹样背景图片
- 音频播放图标资源