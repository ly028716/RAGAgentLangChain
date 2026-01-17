"""
测试API文档配置

验证FastAPI的OpenAPI文档配置是否正确。
"""

import sys
import json
from pathlib import Path

# 添加app目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app


def test_openapi_schema():
    """测试OpenAPI schema生成"""
    print("=" * 60)
    print("测试OpenAPI Schema生成")
    print("=" * 60)
    
    # 获取OpenAPI schema
    schema = app.openapi()
    
    # 验证基本信息
    assert schema["info"]["title"] == app.title
    assert schema["info"]["version"] == app.version
    assert "description" in schema["info"]
    assert "contact" in schema["info"]
    assert "license" in schema["info"]
    
    print(f"✓ 标题: {schema['info']['title']}")
    print(f"✓ 版本: {schema['info']['version']}")
    print(f"✓ 描述长度: {len(schema['info']['description'])} 字符")
    print(f"✓ 联系方式: {schema['info']['contact']}")
    print(f"✓ 许可证: {schema['info']['license']}")
    
    # 验证标签
    assert "tags" in schema
    tags = schema["tags"]
    print(f"\n✓ API标签数量: {len(tags)}")
    for tag in tags:
        print(f"  - {tag['name']}: {tag['description']}")
    
    # 验证路径
    assert "paths" in schema
    paths = schema["paths"]
    print(f"\n✓ API端点数量: {len(paths)}")
    
    # 统计各标签的端点数量
    tag_counts = {}
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                tags_list = details.get("tags", [])
                for tag in tags_list:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    print("\n各模块端点统计:")
    for tag, count in sorted(tag_counts.items()):
        print(f"  - {tag}: {count} 个端点")
    
    # 验证响应定义
    if "components" in schema and "responses" in schema["components"]:
        responses = schema["components"]["responses"]
        print(f"\n✓ 通用响应定义: {len(responses)} 个")
    
    # 验证schemas
    if "components" in schema and "schemas" in schema["components"]:
        schemas = schema["components"]["schemas"]
        print(f"✓ 数据模型定义: {len(schemas)} 个")
        
        # 检查是否有示例
        schemas_with_examples = 0
        for schema_name, schema_def in schemas.items():
            if "examples" in schema_def or "example" in schema_def:
                schemas_with_examples += 1
        print(f"  - 包含示例的模型: {schemas_with_examples} 个")
    
    print("\n" + "=" * 60)
    print("✓ OpenAPI Schema测试通过")
    print("=" * 60)
    
    return schema


def test_docs_urls():
    """测试文档URL配置"""
    print("\n" + "=" * 60)
    print("测试文档URL配置")
    print("=" * 60)
    
    # 检查文档URL
    routes = [route.path for route in app.routes]
    
    if "/docs" in routes:
        print("✓ Swagger UI: http://localhost:8000/docs")
    else:
        print("✗ Swagger UI未启用（生产环境默认禁用）")
    
    if "/redoc" in routes:
        print("✓ ReDoc: http://localhost:8000/redoc")
    else:
        print("✗ ReDoc未启用（生产环境默认禁用）")
    
    if "/openapi.json" in routes:
        print("✓ OpenAPI JSON: http://localhost:8000/openapi.json")
    else:
        print("✗ OpenAPI JSON未启用")
    
    print("=" * 60)


def test_endpoint_documentation():
    """测试端点文档完整性"""
    print("\n" + "=" * 60)
    print("测试端点文档完整性")
    print("=" * 60)
    
    schema = app.openapi()
    paths = schema["paths"]
    
    # 检查每个端点的文档
    endpoints_without_summary = []
    endpoints_without_description = []
    endpoints_without_tags = []
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                endpoint_name = f"{method.upper()} {path}"
                
                if "summary" not in details or not details["summary"]:
                    endpoints_without_summary.append(endpoint_name)
                
                if "description" not in details or not details["description"]:
                    endpoints_without_description.append(endpoint_name)
                
                if "tags" not in details or not details["tags"]:
                    endpoints_without_tags.append(endpoint_name)
    
    total_endpoints = sum(
        1 for path, methods in paths.items()
        for method in methods.keys()
        if method in ["get", "post", "put", "delete", "patch"]
    )
    
    print(f"总端点数: {total_endpoints}")
    print(f"✓ 有摘要的端点: {total_endpoints - len(endpoints_without_summary)}")
    print(f"✓ 有描述的端点: {total_endpoints - len(endpoints_without_description)}")
    print(f"✓ 有标签的端点: {total_endpoints - len(endpoints_without_tags)}")
    
    if endpoints_without_summary:
        print(f"\n⚠ 缺少摘要的端点 ({len(endpoints_without_summary)}):")
        for endpoint in endpoints_without_summary[:5]:
            print(f"  - {endpoint}")
        if len(endpoints_without_summary) > 5:
            print(f"  ... 还有 {len(endpoints_without_summary) - 5} 个")
    
    if endpoints_without_description:
        print(f"\n⚠ 缺少描述的端点 ({len(endpoints_without_description)}):")
        for endpoint in endpoints_without_description[:5]:
            print(f"  - {endpoint}")
        if len(endpoints_without_description) > 5:
            print(f"  ... 还有 {len(endpoints_without_description) - 5} 个")
    
    print("=" * 60)


def save_openapi_schema():
    """保存OpenAPI schema到文件"""
    print("\n" + "=" * 60)
    print("保存OpenAPI Schema")
    print("=" * 60)
    
    schema = app.openapi()
    
    # 保存为JSON
    output_file = Path(__file__).parent / "openapi.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"✓ OpenAPI Schema已保存到: {output_file}")
    print(f"  文件大小: {output_file.stat().st_size / 1024:.2f} KB")
    
    print("=" * 60)


if __name__ == "__main__":
    try:
        # 运行测试
        test_openapi_schema()
        test_docs_urls()
        test_endpoint_documentation()
        save_openapi_schema()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        print("\n访问文档:")
        print("  - Swagger UI: http://localhost:8000/docs")
        print("  - ReDoc: http://localhost:8000/redoc")
        print("  - OpenAPI JSON: http://localhost:8000/openapi.json")
        print("\n提示: 确保应用在DEBUG模式下运行以启用文档")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
