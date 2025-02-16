# 方案目标
能够爬取任何一个网站，我输入一个网页，你返回网页的页面信息或者UI图，我框选出的类型统一进行爬虫
# 框架架构
1. 网页渲染与截图模块
技术栈: Headless Browser (Playwright/Selenium) + 前端Canvas
功能:
输入URL后自动渲染网页（支持JS动态加载）
生成网页全屏截图或DOM结构快照，供用户可视化交互
2. 可视化框选交互模块
技术栈: Web前端 (React/Vue) + 图像坐标映射
功能:
用户在截图/UI图上框选目标区域
关键算法:
将框选的像素坐标映射到DOM元素的XPath/CSS选择器（通过浏览器API获取元素位置信息）
3. 规则智能生成模块
技术栈: DOM解析 (BeautifulSoup/lxml) + 规则泛化
功能:
自动分析框选区域的DOM结构，生成通用选择器（如识别同类元素的共同特征）
支持手动修正选择器（非代码交互，如高亮预览）
4. 任务调度与爬取引擎
技术栈: 异步请求 (aiohttp/httpx) + 反爬策略
功能:
根据规则批量爬取同类页面（自动处理分页、滚动加载）
内置IP轮换、请求频率控制、User-Agent池等反反爬机制
5. 数据输出模块
技术栈: 结构化存储 (Pandas) + API服务 (FastAPI)
功能:
导出JSON/CSV/Excel等格式
提供Webhook或API实时推送数据
# 用户操作流程
输入URL → 系统返回网页截图+DOM分析结果
框选目标元素 → 系统自动生成选择器并高亮同类元素
配置爬取范围（如翻页规则、触发JS事件）
启动任务 → 系统爬取数据并输出

# Web Crawler System Interface Design

## 1. Crawler Core Module (crawler_core)

### 1.1 Spider Interface
```python
class ISpider:
    async def crawl(self, url: str) -> dict:
        """Base crawling interface"""
        pass
    
    async def parse(self, content: str) -> dict:
        """Parse content interface"""
        pass
    
    def validate_url(self, url: str) -> bool:
        """URL validation interface"""
        pass
```

### 1.2 Request Manager Interface
```python
class IRequestManager:
    async def make_request(self, url: str, method: str = "GET", headers: dict = None) -> str:
        """HTTP request interface"""
        pass
    
    def set_proxy(self, proxy: str) -> None:
        """Proxy setting interface"""
        pass
    
    def set_retry_policy(self, max_retries: int, delay: int) -> None:
        """Retry policy setting interface"""
        pass
```

### 1.3 Rate Limiter Interface
```python
class IRateLimiter:
    async def acquire(self, domain: str) -> bool:
        """Rate limit check interface"""
        pass
    
    def update_rate(self, domain: str, requests_per_second: float) -> None:
        """Rate update interface"""
        pass
```

## 2. Data Processing Module (data_processor)

### 2.1 Content Extractor Interface
```python
class IContentExtractor:
    def extract_text(self, html: str) -> str:
        """Text extraction interface"""
        pass
    
    def extract_structured_data(self, content: str) -> dict:
        """Structured data extraction interface"""
        pass
```

### 2.2 Data Classifier Interface
```python
class IDataClassifier:
    def train(self, training_data: list) -> None:
        """Training interface"""
        pass
    
    def classify(self, content: str) -> str:
        """Classification interface"""
        pass
    
    def update_model(self, new_data: list) -> None:
        """Model update interface"""
        pass
```

### 2.3 Data Storage Interface
```python
class IDataStorage:
    async def save(self, data: dict, category: str) -> bool:
        """Data saving interface"""
        pass
    
    async def retrieve(self, query: dict) -> list:
        """Data retrieval interface"""
        pass
    
    async def update(self, query: dict, new_data: dict) -> bool:
        """Data update interface"""
        pass
```

## 3. Task Management Module (task_manager)

### 3.1 Queue Manager Interface
```python
class IQueueManager:
    async def push_task(self, task: dict) -> bool:
        """Task enqueue interface"""
        pass
    
    async def pop_task(self) -> dict:
        """Task dequeue interface"""
        pass
    
    def get_queue_status(self) -> dict:
        """Queue status interface"""
        pass
```

### 3.2 Task Scheduler Interface
```python
class ITaskScheduler:
    def schedule_task(self, task: dict, schedule_time: datetime) -> str:
        """Task scheduling interface"""
        pass
    
    def cancel_task(self, task_id: str) -> bool:
        """Task cancellation interface"""
        pass
    
    def get_scheduled_tasks(self) -> list:
        """Task retrieval interface"""
        pass
```

## 4. Monitoring Module (monitor)

### 4.1 Performance Monitor Interface
```python
class IPerformanceMonitor:
    def record_metrics(self, metrics: dict) -> None:
        """Metrics recording interface"""
        pass
    
    def get_statistics(self, metric_name: str, time_range: tuple) -> dict:
        """Statistics retrieval interface"""
        pass
```

### 4.2 Error Handler Interface
```python
class IErrorHandler:
    def handle_error(self, error: Exception, context: dict) -> None:
        """Error handling interface"""
        pass
    
    def get_error_log(self, start_time: datetime, end_time: datetime) -> list:
        """Error log retrieval interface"""
        pass
```

## 5. Configuration Module (config)

### 5.1 Config Manager Interface
```python
class IConfigManager:
    def load_config(self, config_path: str) -> dict:
        """Configuration loading interface"""
        pass
    
    def update_config(self, config_path: str, new_config: dict) -> bool:
        """Configuration update interface"""
        pass
    
    def get_config_value(self, key: str) -> Any:
        """Configuration value retrieval interface"""
        pass
```

## 6. API Module (api)

### 6.1 REST API Interface
```python
class IRestAPI:
    async def start_crawl(self, params: dict) -> str:
        """Crawl initiation interface"""
        pass
    
    async def get_status(self, task_id: str) -> dict:
        """Status check interface"""
        pass
    
    async def stop_crawl(self, task_id: str) -> bool:
        """Crawl termination interface"""
        pass
```

### 6.2 WebSocket Interface
```python
class IWebSocket:
    async def connect(self, client_id: str) -> bool:
        """Connection interface"""
        pass
    
    async def send_update(self, client_id: str, message: dict) -> bool:
        """Update sending interface"""
        pass
    
    async def close(self, client_id: str) -> bool:
        """Connection closing interface"""
        pass