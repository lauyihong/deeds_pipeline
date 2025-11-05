# MassLand Records Scraper

自动化爬虫脚本，用于从MassLand Records网站提取土地记录metadata信息。

## 📋 功能概述

该脚本能够：
1. 自动访问MassLand Records网站
2. 根据Book和Page编号搜索记录
3. 提取详细的文档metadata信息，包括：
   - 文档详情（Doc. #, File Date, Rec Time, Type Desc., Book/Page, Consideration, Doc. Status）
   - 属性信息（Street #, Street Name, Description）
   - Grantor/Grantee信息

## 🏗️ 架构设计

### 核心类：`MassLandScraper`

脚本采用面向对象设计，主要包含以下组件：

```
MassLandScraper
├── __init__()              # 初始化浏览器驱动
├── navigate_to_search_page()  # 导航到搜索页面
├── setup_search_criteria()     # 设置搜索条件（Office和Search Type）
├── search_by_book_page()      # 执行搜索
├── check_search_results()     # 检查搜索结果
├── click_file_and_extract_metadata()  # 点击结果并提取metadata
├── extract_metadata()        # 提取metadata数据
├── extract_table_data()      # 从表格中提取结构化数据
├── process_csv_file()        # 批量处理CSV文件
├── save_results()            # 保存结果到JSON
└── close()                   # 关闭浏览器
```

## 🔄 工作流程

### 1. 初始化阶段
```python
scraper = MassLandScraper(headless=False)
```
- 创建Chrome浏览器实例
- 配置浏览器选项（窗口大小、用户代理等）
- 初始化WebDriverWait等待对象

### 2. 搜索流程

对于每个Book/Page组合，执行以下步骤：

#### 步骤1: 导航到搜索页面
```
访问: https://www.masslandrecords.com/MiddlesexNorth/D/Default.aspx
等待页面加载完成
```

#### 步骤2: 设置搜索条件
```
1. 设置Office下拉菜单 → "Plans"
2. 设置Search Type下拉菜单 → "Book Search"
3. 等待Ajax更新完成
```

#### 步骤3: 输入搜索参数
```
1. 在Book输入框中输入Book编号
2. 在Page输入框中输入Page编号
3. 点击"Search"按钮
```

#### 步骤4: 等待搜索结果
```
等待DocList1_GridView_Document表格出现
验证搜索结果已加载
```

#### 步骤5: 检查搜索结果
```
通过File Date链接定位搜索结果
统计结果数量
提取第一条结果的基本信息（用于调试）
```

#### 步骤6: 点击File Date链接
```
定位File Date链接（使用多种选择器策略）
使用JavaScript点击（避免StaleElementReferenceException）
等待DocDetails区域加载
```

#### 步骤7: 提取Metadata
```
提取三个主要表格：
1. DocDetails1_GridView_Details - 文档详情
2. DocDetails1_GridView_Property - 属性信息
3. DocDetails1_GridView_GrantorGrantee - Grantor/Grantee信息
```

### 3. 数据提取逻辑

#### `extract_table_data()` 方法
- 从表格中提取表头作为字典的key
- 遍历数据行，将每行转换为字典
- 处理包含链接的单元格，提取链接文本和href
- 返回字典列表格式

#### `extract_metadata()` 方法
- 按顺序提取三个主要表格
- 提取其他DocDetails区域的内容作为备用
- 返回包含所有metadata的字典

## 📁 文件结构

```
test_scrap/
├── massland_scraper.py      # 主脚本
├── massland_input.csv        # 输入文件（Book, Page）
├── massland_output.json      # 输出文件（提取的metadata）
├── requirements.txt          # Python依赖
└── README.md                 # 本文件
```

## 📥 输入格式

### CSV文件格式 (`massland_input.csv`)
```csv
book,page
57,21
51,27
```

**字段说明：**
- `book`: 书籍编号（整数或字符串）
- `page`: 页码（整数或字符串）

## 📤 输出格式

### JSON文件格式 (`massland_output.json`)
```json
[
  {
    "book": "57",
    "page": "21",
    "metadata": {
      "document_details": [
        {
          "Doc. #": "5721",
          "File Date": "10/26/1932",
          "Rec Time": "00:00AM",
          "Type Desc.": "PLAN",
          "Book/Page": "00057/21",
          "Consideration": "",
          "Doc. Status": "Verified/Certified"
        }
      ],
      "property_info": [
        {
          "Street #": "",
          "Street Name": "CHRISTIAN ST",
          "Description": ""
        }
      ],
      "grantor_grantee": [
        {
          "column_0": "MIDDLESEX CO-OPERATIVE BANK-LOWELL",
          "column_0_link": "javascript:__doPostBack(...)",
          "column_1": "Grantor"
        }
      ]
    },
    "status": "success"
  }
]
```

**字段说明：**
- `book`: 输入的Book编号
- `page`: 输入的Page编号
- `metadata`: 提取的metadata字典
  - `document_details`: 文档详情列表
  - `property_info`: 属性信息列表
  - `grantor_grantee`: Grantor/Grantee信息列表
- `status`: 处理状态（"success" 或 "failed"）

## 🚀 使用方法

### 基本使用

```python
from massland_scraper import MassLandScraper

# 创建scraper实例
scraper = MassLandScraper(headless=False)

# 处理CSV文件
results = scraper.process_csv_file("massland_input.csv")

# 保存结果
scraper.save_results(results, "massland_output.json")

# 关闭浏览器
scraper.close()
```

### 命令行使用

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python massland_scraper.py
```

### 集成到Pipeline

#### 方式1: 作为模块导入

```python
from massland_scraper import MassLandScraper
import pandas as pd

def process_land_records(book_page_list):
    """
    处理土地记录列表
    
    Args:
        book_page_list: [(book1, page1), (book2, page2), ...]
    
    Returns:
        list: 包含metadata的结果列表
    """
    scraper = MassLandScraper(headless=True)  # 后台运行
    results = []
    
    try:
        for book, page in book_page_list:
            # 导航到搜索页面
            scraper.navigate_to_search_page()
            
            # 执行搜索
            if scraper.search_by_book_page(book, page):
                # 提取metadata
                metadata = scraper.click_file_and_extract_metadata()
                results.append({
                    'book': book,
                    'page': page,
                    'metadata': metadata,
                    'status': 'success' if metadata and 'error' not in str(metadata) else 'failed'
                })
    finally:
        scraper.close()
    
    return results

# 使用示例
book_pages = [(57, 21), (51, 27)]
results = process_land_records(book_pages)
```

#### 方式2: 批量处理DataFrame

```python
import pandas as pd
from massland_scraper import MassLandScraper

def process_dataframe(df):
    """
    处理包含Book和Page列的DataFrame
    
    Args:
        df: pandas DataFrame，包含'book'和'page'列
    
    Returns:
        DataFrame: 添加了metadata列的新DataFrame
    """
    scraper = MassLandScraper(headless=True)
    results = []
    
    try:
        for _, row in df.iterrows():
            book = str(row['book'])
            page = str(row['page'])
            
            scraper.navigate_to_search_page()
            if scraper.search_by_book_page(book, page):
                metadata = scraper.click_file_and_extract_metadata()
                results.append(metadata)
            else:
                results.append({'error': 'search_failed'})
    finally:
        scraper.close()
    
    df['metadata'] = results
    return df
```

#### 方式3: 异步处理（适合大批量数据）

```python
from concurrent.futures import ThreadPoolExecutor
from massland_scraper import MassLandScraper

def process_single_record(book, page):
    """处理单个记录"""
    scraper = MassLandScraper(headless=True)
    try:
        scraper.navigate_to_search_page()
        if scraper.search_by_book_page(book, page):
            metadata = scraper.click_file_and_extract_metadata()
            return {
                'book': book,
                'page': page,
                'metadata': metadata,
                'status': 'success' if metadata and 'error' not in str(metadata) else 'failed'
            }
        return {'book': book, 'page': page, 'status': 'search_failed'}
    finally:
        scraper.close()

def process_batch(book_page_list, max_workers=3):
    """批量处理（使用线程池）"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda x: process_single_record(x[0], x[1]),
            book_page_list
        ))
    return results
```

## ⚙️ 配置选项

### 初始化参数

```python
MassLandScraper(headless=False)
```

- `headless` (bool): 
  - `False`: 显示浏览器窗口（便于调试）
  - `True`: 后台运行（适合生产环境）

### 自定义等待时间

在脚本中修改以下常量：
```python
self.wait = WebDriverWait(self.driver, 20)  # 默认20秒超时
time.sleep(2)  # 各种等待时间
```

## 🔧 错误处理

脚本包含多层错误处理机制：

1. **重试机制**: 每个记录最多重试3次
2. **浏览器恢复**: 如果浏览器连接丢失，自动重新初始化
3. **多种选择器策略**: 使用多种方法定位元素，提高成功率
4. **JavaScript点击**: 避免StaleElementReferenceException

### 常见错误及解决方案

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `StaleElementReferenceException` | 元素已过期 | 使用JavaScript点击或重新查找元素 |
| `TimeoutException` | 页面加载超时 | 增加等待时间或检查网络连接 |
| `NoSuchElementException` | 找不到元素 | 检查页面结构是否变化 |

## 📊 性能优化建议

1. **批量处理**: 对于大量数据，考虑使用异步处理
2. **缓存机制**: 避免重复搜索相同Book/Page
3. **延迟设置**: 在请求之间添加适当延迟，避免被封IP
4. **资源管理**: 确保在finally块中关闭浏览器

## 🔍 调试技巧

### 启用详细日志
脚本已包含详细的print语句，显示每个步骤的执行状态。

### 使用headless=False模式
```python
scraper = MassLandScraper(headless=False)
```
这样可以观察浏览器的实际行为，便于调试。

### 保存中间状态
```python
# 在搜索后保存页面截图
scraper.driver.save_screenshot(f"search_{book}_{page}.png")

# 保存页面HTML
with open(f"page_{book}_{page}.html", "w") as f:
    f.write(scraper.driver.page_source)
```

## 📝 依赖要求

```
selenium>=4.15.0
```

确保已安装Chrome浏览器和ChromeDriver（Selenium 4.6+会自动管理）。

## 🎯 关键设计决策

1. **使用Selenium**: 因为网站使用Ajax动态加载，需要真实浏览器环境
2. **JavaScript点击**: 避免StaleElementReferenceException问题
3. **多种选择器策略**: 提高元素定位的成功率
4. **结构化数据提取**: 将表格数据转换为字典格式，便于后续处理

## 🔄 Pipeline集成检查清单

- [ ] 确保Chrome浏览器已安装
- [ ] 安装Python依赖: `pip install -r requirements.txt`
- [ ] 准备输入CSV文件（包含book和page列）
- [ ] 根据需要调整等待时间和重试次数
- [ ] 在生产环境中使用`headless=True`
- [ ] 实现错误处理和日志记录
- [ ] 设置适当的延迟以避免被封IP
- [ ] 处理输出JSON数据并集成到下游系统

## 📞 支持

如遇问题，检查：
1. Chrome浏览器版本是否兼容
2. 网络连接是否正常
3. 网站结构是否有变化
4. 查看详细错误日志

## 📄 许可证

本项目仅供学习和研究使用。

