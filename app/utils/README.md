# PDF文档解析器

## 概述

这是一个生产级的PDF文档解析工具，支持从PDF文档中提取文本、图片和表格内容。该工具支持多种输入方式，包括本地文件路径、网络URL、字节数据和文件流，并按页结构化输出整个PDF的内容。

## 主要特性

- **多种输入方式支持**：本地文件路径、网络URL、字节数据、文件流
- **按页结构化输出**：每页内容独立组织，包含文本块、图片和表格
- **资源管理优化**：自动内存管理，定期垃圾回收，防止内存泄漏
- **健壮性设计**：全面的错误处理，确保解析过程的稳定性
- **生产级性能**：支持大文件处理，可配置内存限制
- **丰富的元数据**：提取文档元数据，包括文件大小和校验和

## 安装依赖

```bash
pip install PyMuPDF pdfplumber pypdf pillow tabulate
```

## 基本用法

### 1. 解析本地PDF文件

```python
from app.utils.document_parser import parse_pdf_document

# 解析本地PDF文件
result = parse_pdf_document(
    "path/to/document.pdf",
    extract_images=True,
    extract_tables=True,
    extract_text_blocks=True,
    max_pages=5  # 只处理前5页
)

print(f"解析成功: {result['parse_success']}")
print(f"页数: {result['metadata']['page_count']}")

# 遍历每一页的内容
for page in result['pages']:
    print(f"第 {page['page_number']} 页")
    print(f"文本块数量: {len(page['text_blocks'])}")
    print(f"图片数量: {len(page['images'])}")
    print(f"表格数量: {len(page['tables'])}")
```

### 2. 解析网络PDF文件

```python
# 解析网络PDF文件
result = parse_pdf_document(
    "https://example.com/document.pdf",
    extract_images=False,  # 不提取图片以节省带宽
    extract_tables=True,
    extract_text_blocks=True
)

print(f"来源类型: {result['source_type']}")  # 输出: "url"
```

### 3. 解析字节数据

```python
# 读取PDF文件为字节数据
with open("path/to/document.pdf", 'rb') as f:
    pdf_bytes = f.read()

# 解析字节数据
result = parse_pdf_document(
    pdf_bytes,
    extract_images=True,
    extract_tables=True,
    extract_text_blocks=True,
    file_name="example.pdf"
)

print(f"来源类型: {result['source_type']}")  # 输出: "bytes"
```

### 4. 解析文件流

```python
import io

# 打开PDF文件作为文件流
with open("path/to/document.pdf", 'rb') as f:
    stream = io.BytesIO(f.read())
    
    # 解析文件流
    result = parse_pdf_document(
        stream,
        extract_images=True,
        extract_tables=True,
        extract_text_blocks=True,
        file_name="stream_example.pdf"
    )
    
    print(f"来源类型: {result['source_type']}")  # 输出: "stream"
```

## 提取特定内容

### 只提取文本

```python
from app.utils.document_parser import extract_text_from_pdf

text = extract_text_from_pdf("path/to/document.pdf")
print(f"提取的文本长度: {len(text)} 字符")
```

### 只提取图片

```python
from app.utils.document_parser import extract_images_from_pdf

images = extract_images_from_pdf("path/to/document.pdf")
print(f"提取的图片数量: {len(images)}")

# 显示第一张图片的信息
if images:
    img = images[0]
    print(f"图片内容类型: {img['content_type']}")
    print(f"图片格式: {img['format']}")
    print(f"图片尺寸: {img['width']}x{img['height']}")
```

### 只提取表格

```python
from app.utils.document_parser import extract_tables_from_pdf

tables = extract_tables_from_pdf("path/to/document.pdf")
print(f"提取的表格数量: {len(tables)}")

# 显示第一个表格
if tables:
    table = tables[0]
    print(f"表格位置: 第{table['page']}页")
    print(f"表格大小: {table['rows']}行 x {table['columns']}列")
    print("表格内容:")
    print(table['markdown'])
```

### 提取结构化文本块

```python
from app.utils.document_parser import extract_text_blocks_from_pdf

text_blocks = extract_text_blocks_from_pdf("path/to/document.pdf")
print(f"提取的文本块数量: {len(text_blocks)}")

# 显示前3个文本块
for i, block in enumerate(text_blocks[:3]):
    print(f"文本块 {i+1}:")
    print(f"  位置: 第{block['page']}页")
    print(f"  字体: {block['font_name']}")
    print(f"  字号: {block['font_size']}")
    print(f"  文本: {block['text'][:50]}...")
```

### 获取文档元数据

```python
from app.utils.document_parser import get_pdf_metadata

metadata = get_pdf_metadata("path/to/document.pdf")
print(f"文档标题: {metadata['title']}")
print(f"文档作者: {metadata['author']}")
print(f"页数: {metadata['page_count']}")
print(f"文件大小: {metadata['file_size']} 字节")
print(f"MD5校验和: {metadata['checksum']}")
```

## 高级用法

### 自定义解析器实例

```python
from app.utils.document_parser import DocumentParser

# 创建自定义解析器实例，限制内存使用为256MB
parser = DocumentParser(max_memory_mb=256)

# 使用自定义解析器解析文档
result = parser.parse_document(
    "path/to/document.pdf",
    extract_images=True,
    extract_tables=True,
    extract_text_blocks=True,
    max_pages=10  # 只处理前10页
)

# 保存提取的图片
if result['parse_success']:
    all_images = []
    for page in result['pages']:
        all_images.extend(page['images'])
    
    if all_images:
        print(f"共提取 {len(all_images)} 张图片")
        # 显示前3张图片的信息
        for i, img in enumerate(all_images[:3]):
            print(f"图片 {i+1}: 内容类型={img['content_type']}, 格式={img['format']}, 尺寸={img['width']}x{img['height']}")

# 清理资源
parser.cleanup()
```

## 数据结构

### 解析结果结构

```python
{
    'file_path': str,           # 文件路径
    'file_name': str,           # 文件名
    'source_type': str,         # 输入类型: "local", "url", "bytes", "stream"
    'metadata': {               # 文档元数据
        'title': str,
        'author': str,
        'subject': str,
        'creator': str,
        'producer': str,
        'creation_date': str,
        'modification_date': str,
        'page_count': int,
        'file_size': int,
        'checksum': str
    },
    'pages': [                 # 页面内容列表
        {
            'page_number': int,     # 页码
            'width': float,         # 页面宽度
            'height': float,        # 页面高度
            'rotation': int,        # 页面旋转角度
            'text_blocks': [        # 文本块列表
                {
                    'page': int,
                    'index': int,
                    'text': str,
                    'bbox': tuple,       # 边界框 (x0, y0, x1, y1)
                    'font_size': float,
                    'font_name': str,
                    'is_bold': bool,
                    'is_italic': bool
                }
            ],
            'images': [             # 图片列表
                {
                    'page': int,
                    'index': int,
                    'width': int,
                    'height': int,
                    'colorspace': str,
                    'base64': str,        # 图片Base64编码
                    'content_type': str,    # 图片内容类型: "text", "chart", "photo", "logo", "other"
                    'format': str,         # 图片格式: "PNG", "JPEG"等
                    'size_ratio': float,
                    'bbox': tuple         # 边界框 (x0, y0, x1, y1)
                }
            ],
            'tables': [             # 表格列表
                {
                    'page': int,
                    'index': int,
                    'rows': int,
                    'columns': int,
                    'data': list,         # 表格数据
                    'markdown': str,      # Markdown格式的表格
                    'bbox': tuple         # 边界框 (x0, y0, x1, y1)
                }
            ],
            'raw_text': str          # 页面原始文本
        }
    ],
    'is_scanned': bool,         # 是否为扫描文档
    'parse_success': bool,       # 解析是否成功
    'error_message': str,        # 错误信息
    'processing_time': float     # 处理时间（秒）
}
```

## 性能优化

1. **内存管理**：
   - 定期进行垃圾回收，控制内存使用
   - 可配置最大内存限制
   - 自动清理临时文件
   - 图片数据只保留base64编码，降低内存占用
   - 网络资源直接在内存中处理，避免不必要的磁盘I/O

2. **大文件处理**：
   - 支持限制处理页数
   - 按页处理，避免一次性加载整个文档
   - 提供流式处理函数，分批处理大型PDF

3. **资源释放**：
   - 自动关闭文件句柄
   - 释放图片资源
   - 提供清理方法
   - 跟踪所有临时文件，确保完整清理

4. **网络下载优化**：
   - 支持重试机制，提高下载成功率
   - 指数退避策略，避免频繁请求
   - 下载大小限制，防止资源耗尽
   - 直接在内存中处理，避免磁盘I/O

## 错误处理

解析器具有全面的错误处理机制：

- 输入验证：检查文件格式和有效性
- 异常捕获：捕获并记录处理过程中的异常
- 资源清理：确保在出错时正确释放资源
- 错误报告：提供详细的错误信息

## 注意事项

1. 对于大型PDF文件，建议使用`max_pages`参数限制处理页数
2. 提取图片会增加内存使用，对于内存受限环境，可以设置`extract_images=False`
3. 网络URL解析需要稳定的网络连接
4. 临时文件会在解析完成后自动清理，但也可以手动调用`cleanup()`方法

## 示例代码

完整的使用示例请参考`document_parser_example.py`文件。
