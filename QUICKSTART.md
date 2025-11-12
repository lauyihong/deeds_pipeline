# Quick Start Guide

## 快速开始指南

### 1. 安装依赖

```bash
cd /Users/yifeng/Documents/GitHub/deeds_pipeline
pip install -r requirements.txt
```

### 2. 配置API密钥

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

### 3. 实现TODO函数

框架已经搭建完成，你需要实现以下标记为 `# TODO` 的函数：

#### Step 1: `deeds_pipeline/step1_json_reformat.py`
- `reformat_deed_reviews()` - 将deed_review_id转换为deed_id索引

#### Step 2: `deeds_pipeline/step2_ocr_extraction.py`
- `extract_text_with_google_vision()` - Google Vision OCR
- `detect_restrictive_covenant()` - Mistral-RRC契约检测
- `extract_deed_info_with_gemini()` - Gemini信息提取

#### Step 3: `deeds_pipeline/step3_scraper.py`
- `initialize_scraper()` - 初始化MassLandScraper
- `scrape_massland_record()` - 爬取单条记录

#### Step 4: `deeds_pipeline/step4_geolocation.py`
- `initialize_clustering_validator()` - 初始化StreetClusteringValidator
- `geocode_streets()` - 地理编码

### 4. 运行Pipeline

```bash
# 运行完整pipeline
python script/run_pipeline.py

# 只运行某几个步骤
python script/run_pipeline.py --start 1 --stop 3

# 运行单个步骤测试
python -m deeds_pipeline.step1_json_reformat
```

### 5. 查看结果

输出文件位于 `output/` 目录：
- `step1_reformatted_by_deed_id.json` - 重格式化的数据
- `step2_ocr_extracted.json` - OCR和提取结果
- `step3_scraper_data.json` - 爬虫数据
- `step4_geolocation.json` - 地理编码结果
- `step5_final_integrated.json` - 最终JSON输出
- `step5_final_integrated.csv` - 最终CSV输出（便于分析）

### 6. 查看日志

日志文件位于 `logs/` 目录：
- `pipeline.log` - 主pipeline日志
- `step1.log`, `step2.log`, ... - 各步骤详细日志

## 目录结构

```
deeds_pipeline/
├── data/                          # 输入数据
├── deeds_pipeline/                # 主包
│   ├── config.py                  # ✅ 配置文件（已完成）
│   ├── step1_json_reformat.py    # ⚠️ TODO: reformat_deed_reviews()
│   ├── step2_ocr_extraction.py   # ⚠️ TODO: 3个OCR/AI函数
│   ├── step3_scraper.py          # ⚠️ TODO: 2个爬虫函数
│   ├── step4_geolocation.py      # ⚠️ TODO: 2个地理编码函数
│   ├── step5_integration.py      # ✅ 数据整合（已完成）
│   └── utils/                     # ✅ 工具函数（已完成）
├── script/
│   └── run_pipeline.py           # ✅ 主运行脚本（已完成）
├── output/                        # 输出目录
├── cache/                         # 缓存目录
├── logs/                          # 日志目录
└── requirements.txt               # ✅ 依赖列表（已完成）
```

## 实现建议

### Step 1 实现提示
参考 `other_repo/` 中的数据结构，使用字典分组：
```python
deed_dict = {}
for review in input_data:
    deed_id = str(review["deed_id"])
    if deed_id not in deed_dict:
        deed_dict[deed_id] = {"deed_id": deed_id, "review_ids": []}
    deed_dict[deed_id]["review_ids"].append(review["deed_review_id"])
    # 合并其他字段...
```

### Step 2 实现提示
直接复用 `other_repo/mistral_rrc_updated.ipynb` 中的代码：
- 已有完整的Google Vision调用示例
- 已有Mistral-RRC模型加载和推理代码
- 已有Gemini API调用示例

### Step 3 实现提示
直接导入 `other_repo/test_scrap/massland_scraper.py`：
```python
from other_repo.test_scrap.massland_scraper import MassLandScraper
```

### Step 4 实现提示
直接导入 `other_repo/deed_geo_indexing/` 中的validator：
```python
from app.services.street_clustering_validator import StreetClusteringValidator
```

## 注意事项

1. **API限制**：注意Google Vision和Gemini的API调用限制
2. **缓存**：第一次运行会较慢，后续会使用缓存
3. **Chrome**：Step 3需要Chrome浏览器
4. **异步**：Step 4使用异步函数，框架已处理

## 调试技巧

```bash
# 设置Chrome为可见模式（调试Step 3）
# 在 config.py 中设置：CHROME_HEADLESS = False

# 禁用缓存（重新处理所有数据）
# 在 config.py 中设置：ENABLE_CACHE = False

# 调整日志级别
# 在 config.py 中设置：LOG_LEVEL = "DEBUG"
```

## 下一步

1. ✅ 框架已完成
2. ⚠️ 实现8个TODO函数
3. 🚀 运行测试
4. 📊 分析结果

