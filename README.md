# Quant Crawler

一个强大的异步网络爬虫框架，专注于图片、视频和文章的爬取。

## 特点

- 异步爬取：使用 `asyncio` 和 `aiohttp` 实现高效的异步爬取
- 模块化设计：清晰的接口定义和组件分离
- 可扩展性：基于接口的设计便于扩展
- 错误处理：完善的错误处理和日志记录
- 性能监控：内置性能指标收集
- 速率限制：内置请求速率控制

## 安装

```bash
pip install -r requirements.txt
```

## 目录结构

```
quant_crawler/
├── config/          # 配置文件
├── crawler_core/    # 爬虫核心组件
├── data_processor/  # 数据处理组件
├── monitor/         # 监控组件
├── task_manager/    # 任务管理组件
├── interfaces.py    # 接口定义
└── core.py         # 核心实现

examples/           # 示例代码
├── basic_usage.py      # 基本使用示例
├── dribbble_crawler.py # Dribbble 图片爬虫示例
└── video_crawler.py    # 视频爬虫示例

tests/             # 测试用例
├── conftest.py           # Pytest 配置
├── test_spider.py        # Spider 测试
├── test_request_manager.py  # RequestManager 测试
└── test_content_extractor.py # ContentExtractor 测试
```

## 使用示例

### 基本使用

```python
from quant_crawler.crawler_core.spider import Spider
from quant_crawler.crawler_core.request_manager import RequestManager

async def main():
    spider = Spider(RequestManager())
    content = await spider.crawl("https://example.com")
    print(content)
```

### 图片爬虫

```python
from quant_crawler.data_processor.content_extractor import ContentExtractor

async def crawl_images():
    extractor = ContentExtractor()
    images = await extractor.extract_images(html, base_url, download=True)
    print(f"Found {len(images)} images")
```

### 视频爬虫

```python
from quant_crawler.data_processor.content_extractor import ContentExtractor

async def crawl_videos():
    extractor = ContentExtractor()
    videos = await extractor.extract_videos(html, base_url, download=True)
    print(f"Found {len(videos)} videos")
```

## 测试

运行所有测试：

```bash
pytest tests/
```

## 许可证

MIT License
