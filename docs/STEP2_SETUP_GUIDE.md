# Step 2 设置指南

## 当前状态

✅ **已完成**:
- 代码导入问题已修复（添加了 transformers 导入）
- 环境变量已配置（.env 文件）
- 所需包已安装

⚠️ **需要注意**:
1. **Numpy版本冲突** - 环境中有包依赖冲突
2. **Gemini API配额** - 当前API密钥已达到免费额度限制
3. **Google Cloud Vision认证** - 需要运行 gcloud 命令

---

## 需要您执行的步骤

### 1. 配置 Google Cloud Vision 认证

由于您选择使用 `gcloud auth`，需要运行：

```bash
# 安装 Google Cloud SDK (如果还没安装)
# https://cloud.google.com/sdk/docs/install

# 然后运行认证
gcloud auth application-default login

# 这会打开浏览器让您登录，完成后会自动配置凭证
```

**或者** 移除 .env 中的这一行（因为凭证文件不存在）：
```bash
# 注释掉或删除这一行
# GOOGLE_APPLICATION_CREDENTIALS=/Users/yifeng/Documents/GitHub/deeds_pipeline/vision-credentials.json
```

### 2. Gemini API 配额问题

测试显示您的 API 密钥已达到免费配额限制：
```
429 You exceeded your current quota
Please retry in 56 seconds
```

**解决方案**:
- **选项 A**: 等待约1分钟后重试（免费额度会重置）
- **选项 B**: 使用不同的模型（如 `gemini-1.5-flash` 而不是 `gemini-2.0-flash-exp`）
- **选项 C**: 申请更高配额或付费计划

我已在代码中使用 `gemini-2.0-flash-exp`，您可能需要切换到 `gemini-1.5-flash`。

### 3. Numpy 兼容性问题（可选）

环境中存在包版本冲突。推荐方案：

**选项 A - 创建新的干净conda环境** (推荐):
```bash
# 创建新环境
conda create -n deeds_step2 python=3.10 -y

# 激活环境
conda activate deeds_step2

# 安装依赖
cd /Users/yifeng/Documents/GitHub/deeds_pipeline
pip install -r requirements.txt
```

**选项 B - 降级numpy** (可能影响其他项目):
```bash
pip install "numpy<2.0,>=1.24"
pip install --force-reinstall scikit-learn
```

**选项 C - 忽略警告** (对Step 2影响较小):
- 这些冲突主要影响 streamlit、matplotlib 等
- Step 2 的核心功能（OCR、Gemini）应该仍能工作
- 只有在实际运行时遇到错误才需要修复

---

## 快速测试（不需要模型）

如果您想快速验证基本配置，可以只测试 API 连接：

```python
# test_api_only.py
import os
from dotenv import load_dotenv

load_dotenv()

# 测试 Gemini API
import google.generativeai as genai
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
print("✓ Gemini API configured")

# 测试 Vision API
from google.cloud import vision
from google.api_core.client_options import ClientOptions

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
client_options = ClientOptions(quota_project_id=project_id)
client = vision.ImageAnnotatorClient(client_options=client_options)
print("✓ Vision API client created")

print("\n✅ 基本 API 配置成功!")
```

运行：
```bash
python test_api_only.py
```

---

## 在 Notebook 中使用 Step 2

由于 transformers 模型加载可能有兼容性问题，建议：

### 方案 A - 跳过 Mistral 模型（临时方案）

修改 `step2_ocr_extraction.py` 第52-53行，注释掉模型加载：

```python
# 暂时注释掉模型加载
# tokenizer = AutoTokenizer.from_pretrained("reglab-rrc/mistral-rrc")
# model = AutoModelForCausalLM.from_pretrained("reglab-rrc/mistral-rrc", trust_remote_code=True)
```

并修改 `detect_restrictive_covenant` 函数返回默认值：

```python
def detect_restrictive_covenant(text: str) -> Dict[str, any]:
    # 临时：跳过 Mistral 模型，返回简单关键词检测
    keywords = ["race", "racial", "Caucasian", "white", "negro", "colored", "covenant"]
    detected = any(kw.lower() in text.lower() for kw in keywords)

    return {
        "covenant_detected": detected,
        "raw_passage": "N/A (model skipped)",
        "corrected_quotation": "N/A (model skipped)",
    }
```

这样您仍可以使用 OCR 和 Gemini 提取功能，只是契约检测会使用简单的关键词匹配。

### 方案 B - 只使用 Step 3-5

您的 notebook 已经成功运行了 Step 3-5：
- Step 3: 网页抓取 ✅
- Step 4: 地理编码 ✅
- Step 5: 数据整合 ✅

您可以跳过 Step 2（OCR），直接使用原始数据继续 pipeline。

---

## 推荐的下一步

### 立即可行的方案：

1. **配置 Vision API 认证**
   ```bash
   gcloud auth application-default login
   ```

2. **等待 Gemini API 配额重置** (约1分钟)

3. **运行简化测试**
   ```bash
   python test_step2.py
   ```

### 长期方案：

1. **创建干净的 conda 环境**（避免包冲突）
2. **首次运行时下载 Mistral 模型**（需要 15-20GB 空间）
3. **配置 Google Cloud 付费账户**（如果需要大量使用）

---

## 已修复的文件

1. ✅ `deeds_pipeline/step2_ocr_extraction.py` - 添加了缺失的导入
2. ✅ `.env` - 已配置 API 密钥
3. ✅ `.env.example` - 更新为正确的变量名
4. ✅ `test_step2.py` - 创建了完整的测试脚本

---

## 故障排除

### 问题：import transformers 失败
**解决方案**:
```bash
pip install "numpy<2.0,>=1.24"
pip install --force-reinstall scikit-learn transformers
```

### 问题：Vision API 认证失败
**解决方案**:
```bash
gcloud auth application-default login
```

### 问题：Gemini API 配额超限
**解决方案**: 等待配额重置或切换到其他模型

---

## 需要帮助？

如果遇到问题，请提供：
1. 错误消息的完整输出
2. 运行的命令
3. Python 版本（`python --version`）
4. 包版本（`pip list | grep -E "google|transformers|torch"`）
