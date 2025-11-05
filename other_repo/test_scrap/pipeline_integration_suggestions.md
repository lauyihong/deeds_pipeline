# Pipeline Integration Suggestions

## 1. 模块化和接口设计

### 建议：创建统一的接口适配器

```python
# pipeline_interface.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Iterator

class ScraperInterface(ABC):
    """统一接口，便于与其他pipeline组件集成"""
    
    @abstractmethod
    def process_record(self, book: str, page: str) -> Dict:
        """处理单条记录"""
        pass
    
    @abstractmethod
    def process_batch(self, records: List[Dict]) -> Iterator[Dict]:
        """批量处理记录"""
        pass
    
    @abstractmethod
    def validate_result(self, result: Dict) -> bool:
        """验证结果完整性"""
        pass
```

### 建议：添加结果验证函数

```python
def validate_metadata(result: Dict) -> Dict[str, bool]:
    """验证提取的metadata是否完整"""
    validation = {
        "has_document_details": bool(result.get("metadata", {}).get("document_details")),
        "has_search_info": bool(result.get("metadata", {}).get("search_result_info")),
        "has_town": bool(result.get("metadata", {}).get("search_result_info", {}).get("town")),
        "has_file_date": bool(result.get("metadata", {}).get("search_result_info", {}).get("file_date")),
        "status_success": result.get("status") == "success"
    }
    return validation
```

## 2. 配置管理

### 建议：创建配置文件

```yaml
# config.yaml
scraper:
  headless: true
  timeout: 20
  retry_attempts: 3
  delay_between_requests: 2
  
  search_criteria:
    office: "Plans"
    search_type: "Book Search"
  
  output:
    format: "json"  # json, csv, parquet
    include_raw_html: false
    
  validation:
    required_fields: ["town", "file_date", "book_page"]
    strict_mode: false
```

## 3. 数据标准化和清洗

### 建议：添加数据标准化函数

```python
def normalize_metadata(metadata: Dict) -> Dict:
    """标准化metadata格式，便于下游处理"""
    normalized = {
        "book": metadata.get("book", ""),
        "page": metadata.get("page", ""),
        "file_date": None,
        "rec_time": None,
        "book_page": None,
        "type_desc": None,
        "town": None,
        "document_details": [],
        "property_info": [],
        "grantor_grantee": []
    }
    
    # Extract from search_result_info
    search_info = metadata.get("metadata", {}).get("search_result_info", {})
    normalized.update({
        "file_date": search_info.get("file_date"),
        "rec_time": search_info.get("rec_time"),
        "book_page": search_info.get("book_page"),
        "type_desc": search_info.get("type_desc"),
        "town": search_info.get("town")
    })
    
    # Extract from document_details
    doc_details = metadata.get("metadata", {}).get("document_details", [])
    if doc_details:
        normalized["document_details"] = doc_details
    
    # Extract property and grantor info
    normalized["property_info"] = metadata.get("metadata", {}).get("property_info", [])
    normalized["grantor_grantee"] = metadata.get("metadata", {}).get("grantor_grantee", [])
    
    return normalized
```

## 4. 错误处理和重试策略

### 建议：增强错误分类

```python
class ScrapingError(Exception):
    """Base exception for scraping errors"""
    pass

class SearchFailedError(ScrapingError):
    """Search operation failed"""
    pass

class MetadataExtractionError(ScrapingError):
    """Failed to extract metadata"""
    pass

class NetworkError(ScrapingError):
    """Network/connection error"""
    pass

def classify_error(error: Exception) -> str:
    """分类错误类型，便于下游处理"""
    error_str = str(error).lower()
    if "timeout" in error_str or "connection" in error_str:
        return "network_error"
    elif "search" in error_str or "no results" in error_str:
        return "search_error"
    elif "metadata" in error_str or "extract" in error_str:
        return "extraction_error"
    else:
        return "unknown_error"
```

## 5. 日志和监控

### 建议：结构化日志

```python
import logging
import json
from datetime import datetime

class PipelineLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
    def log_record(self, book: str, page: str, status: str, 
                   duration: float, metadata: Dict = None):
        """记录单条记录的处理结果"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "book": book,
            "page": page,
            "status": status,
            "duration_seconds": duration,
            "has_town": bool(metadata and metadata.get("search_result_info", {}).get("town")),
            "has_document_details": bool(metadata and metadata.get("document_details"))
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_batch_summary(self, total: int, success: int, failed: int, 
                         duration: float):
        """记录批量处理摘要"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "type": "batch_summary",
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0,
            "duration_seconds": duration
        }
        self.logger.info(json.dumps(summary))
```

## 6. 缓存机制

### 建议：添加结果缓存

```python
import hashlib
import json
from pathlib import Path

class ResultCache:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, book: str, page: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{book}_{page}".encode()).hexdigest()
    
    def get(self, book: str, page: str) -> Optional[Dict]:
        """从缓存获取结果"""
        cache_file = self.cache_dir / f"{self._get_cache_key(book, page)}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def set(self, book: str, page: str, result: Dict):
        """保存结果到缓存"""
        cache_file = self.cache_dir / f"{self._get_cache_key(book, page)}.json"
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
```

## 7. 批量处理优化

### 建议：添加进度跟踪

```python
from tqdm import tqdm

class BatchProcessor:
    def __init__(self, scraper, cache=None, logger=None):
        self.scraper = scraper
        self.cache = cache
        self.logger = logger
    
    def process_with_progress(self, records: List[Dict], 
                             show_progress: bool = True) -> List[Dict]:
        """带进度条的批量处理"""
        results = []
        iterator = tqdm(records) if show_progress else records
        
        for record in iterator:
            book = record.get("book")
            page = record.get("page")
            
            # Check cache first
            if self.cache:
                cached = self.cache.get(book, page)
                if cached:
                    results.append(cached)
                    continue
            
            # Process record
            result = self.scraper.process_record(book, page)
            results.append(result)
            
            # Cache result
            if self.cache and result.get("status") == "success":
                self.cache.set(book, page, result)
        
        return results
```

## 8. 数据导出格式

### 建议：支持多种输出格式

```python
import pandas as pd

def export_to_dataframe(results: List[Dict]) -> pd.DataFrame:
    """将结果转换为DataFrame，便于下游分析"""
    rows = []
    for result in results:
        row = {
            "book": result.get("book"),
            "page": result.get("page"),
            "status": result.get("status"),
        }
        
        # Flatten search_result_info
        search_info = result.get("metadata", {}).get("search_result_info", {})
        row.update({
            "file_date": search_info.get("file_date"),
            "rec_time": search_info.get("rec_time"),
            "book_page": search_info.get("book_page"),
            "type_desc": search_info.get("type_desc"),
            "town": search_info.get("town")
        })
        
        # Flatten document_details (first record)
        doc_details = result.get("metadata", {}).get("document_details", [])
        if doc_details:
            row.update(doc_details[0])
        
        rows.append(row)
    
    return pd.DataFrame(rows)

def export_to_parquet(results: List[Dict], output_file: str):
    """导出为Parquet格式（适合大数据处理）"""
    df = export_to_dataframe(results)
    df.to_parquet(output_file, index=False)
```

## 9. API接口（如果需要）

### 建议：创建REST API包装

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
scraper = MassLandScraper(headless=True)

@app.route('/api/scrape', methods=['POST'])
def scrape_single():
    """API端点：处理单条记录"""
    data = request.json
    book = data.get('book')
    page = data.get('page')
    
    result = scraper.process_record(book, page)
    return jsonify(result)

@app.route('/api/scrape/batch', methods=['POST'])
def scrape_batch():
    """API端点：批量处理"""
    data = request.json
    records = data.get('records', [])
    
    results = []
    for record in records:
        result = scraper.process_record(record['book'], record['page'])
        results.append(result)
    
    return jsonify({"results": results})
```

## 10. 测试框架

### 建议：添加单元测试和集成测试

```python
# tests/test_scraper.py
import unittest
from unittest.mock import Mock, patch

class TestMassLandScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = MassLandScraper(headless=True)
    
    def test_extract_search_result_row_info(self):
        # Mock HTML structure
        mock_row = Mock()
        # ... setup mock
        
        result = self.scraper.extract_search_result_row_info()
        self.assertIn("town", result)
        self.assertIn("file_date", result)
    
    def test_normalize_metadata(self):
        raw_metadata = {
            "book": "57",
            "page": "21",
            "metadata": {
                "search_result_info": {
                    "town": "LOWELL",
                    "file_date": "10/26/1932"
                }
            }
        }
        normalized = normalize_metadata(raw_metadata)
        self.assertEqual(normalized["town"], "LOWELL")
```

## 11. 监控和指标

### 建议：添加性能指标收集

```python
import time
from collections import defaultdict

class MetricsCollector:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
    
    def start_timer(self, operation: str, book: str, page: str):
        """开始计时"""
        key = f"{operation}_{book}_{page}"
        self.start_times[key] = time.time()
    
    def end_timer(self, operation: str, book: str, page: str):
        """结束计时并记录"""
        key = f"{operation}_{book}_{page}"
        if key in self.start_times:
            duration = time.time() - self.start_times[key]
            self.metrics[operation].append(duration)
            del self.start_times[key]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {}
        for operation, durations in self.metrics.items():
            if durations:
                stats[operation] = {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations)
                }
        return stats
```

## 12. 集成建议总结

### 优先级高（立即实施）：
1. ✅ **数据标准化函数** - 确保输出格式统一
2. ✅ **结果验证函数** - 确保数据质量
3. ✅ **错误分类** - 便于下游处理错误
4. ✅ **结构化日志** - 便于追踪和调试

### 优先级中（短期实施）：
5. ✅ **缓存机制** - 避免重复请求
6. ✅ **批量处理优化** - 提高效率
7. ✅ **配置管理** - 便于不同环境部署
8. ✅ **进度跟踪** - 用户体验

### 优先级低（长期优化）：
9. ✅ **API接口** - 如果需要微服务架构
10. ✅ **测试框架** - 提高代码质量
11. ✅ **性能监控** - 优化性能瓶颈

## 13. Pipeline集成示例

```python
# pipeline_example.py
from massland_scraper import MassLandScraper
from pipeline_utils import normalize_metadata, validate_metadata, ResultCache, PipelineLogger

def run_pipeline(input_file: str, output_file: str):
    """完整的pipeline示例"""
    # 初始化组件
    scraper = MassLandScraper(headless=True)
    cache = ResultCache("cache")
    logger = PipelineLogger("pipeline")
    
    # 读取上游数据
    records = read_input_records(input_file)  # 你的上游函数
    
    # 处理每条记录
    results = []
    for record in records:
        book = record["book"]
        page = record["page"]
        
        # 检查缓存
        cached = cache.get(book, page)
        if cached:
            results.append(cached)
            continue
        
        # 处理记录
        start_time = time.time()
        result = scraper.process_record(book, page)
        duration = time.time() - start_time
        
        # 标准化和验证
        normalized = normalize_metadata(result)
        validation = validate_metadata(normalized)
        
        # 记录日志
        logger.log_record(book, page, result["status"], duration, normalized)
        
        # 缓存成功的结果
        if result["status"] == "success":
            cache.set(book, page, normalized)
        
        results.append(normalized)
    
    # 导出结果（传递给下游）
    export_results(results, output_file)  # 你的下游函数
    
    return results
```

## 14. 依赖管理

建议添加 `requirements.txt` 的完整版本：

```txt
selenium>=4.15.0
pandas>=1.5.0
pyyaml>=6.0
tqdm>=4.64.0
flask>=2.3.0  # 如果需要API
pytest>=7.4.0  # 如果需要测试
```

## 15. 文档更新

建议在README中添加：
- Pipeline集成指南
- 数据格式规范
- 错误处理指南
- 性能优化建议

