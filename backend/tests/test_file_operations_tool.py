"""
文件操作工具测试
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from app.langchain_integration.tools.file_operations_tool import FileOperationsTool


@pytest.fixture
def temp_workspace():
    """创建临时工作目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_tool(temp_workspace):
    """创建文件操作工具实例"""
    tool = FileOperationsTool()
    tool.base_path = temp_workspace
    return tool


class TestFileOperationsTool:
    """文件操作工具测试类"""

    def test_tool_initialization(self, file_tool):
        """测试工具初始化"""
        assert file_tool.name == "file_operations"
        assert file_tool.base_path is not None
        assert "文件系统操作" in file_tool.description

    def test_write_file_success(self, file_tool):
        """测试写入文件成功"""
        result = file_tool._run(
            operation="write",
            path="test.txt",
            content="Hello, World!"
        )

        assert "成功写入文件" in result
        assert Path(file_tool.base_path, "test.txt").exists()

    def test_read_file_success(self, file_tool):
        """测试读取文件成功"""
        # 先写入文件
        file_tool._run(operation="write", path="test.txt", content="Test content")

        # 读取文件
        result = file_tool._run(operation="read", path="test.txt")

        assert "文件内容" in result
        assert "Test content" in result

    def test_read_nonexistent_file(self, file_tool):
        """测试读取不存在的文件"""
        result = file_tool._run(operation="read", path="nonexistent.txt")

        assert "错误" in result
        assert "不存在" in result

    def test_read_large_file(self, file_tool):
        """测试读取大文件（超过10MB限制）"""
        # 创建一个大文件
        large_file = Path(file_tool.base_path, "large.txt")
        with open(large_file, "w") as f:
            # 写入超过10MB的内容
            f.write("x" * (11 * 1024 * 1024))

        result = file_tool._run(operation="read", path="large.txt")

        assert "错误" in result
        assert "文件过大" in result

    def test_list_directory_success(self, file_tool):
        """测试列出目录成功"""
        # 创建一些文件
        file_tool._run(operation="write", path="file1.txt", content="content1")
        file_tool._run(operation="write", path="file2.txt", content="content2")

        result = file_tool._run(operation="list", path=".")

        assert "目录内容" in result
        assert "file1.txt" in result
        assert "file2.txt" in result

    def test_list_empty_directory(self, file_tool):
        """测试列出空目录"""
        result = file_tool._run(operation="list", path=".")

        assert "目录为空" in result

    def test_check_file_exists(self, file_tool):
        """测试检查文件存在"""
        # 创建文件
        file_tool._run(operation="write", path="test.txt", content="content")

        result = file_tool._run(operation="exists", path="test.txt")

        assert "存在" in result
        assert "文件" in result

    def test_check_file_not_exists(self, file_tool):
        """测试检查文件不存在"""
        result = file_tool._run(operation="exists", path="nonexistent.txt")

        assert "不存在" in result

    def test_write_without_content(self, file_tool):
        """测试写入操作缺少content参数"""
        result = file_tool._run(operation="write", path="test.txt")

        assert "错误" in result
        assert "content" in result

    def test_invalid_operation(self, file_tool):
        """测试无效的操作类型"""
        result = file_tool._run(operation="invalid", path="test.txt")

        assert "错误" in result
        assert "不支持的操作类型" in result

    def test_path_traversal_attack(self, file_tool):
        """测试路径遍历攻击防护"""
        result = file_tool._run(
            operation="read",
            path="../../../etc/passwd"
        )

        assert "错误" in result
        assert "不允许访问" in result

    def test_write_creates_parent_directories(self, file_tool):
        """测试写入文件时自动创建父目录"""
        result = file_tool._run(
            operation="write",
            path="subdir/test.txt",
            content="content"
        )

        assert "成功写入文件" in result
        assert Path(file_tool.base_path, "subdir", "test.txt").exists()

    def test_read_directory_as_file(self, file_tool):
        """测试将目录当作文件读取"""
        # 创建目录
        Path(file_tool.base_path, "testdir").mkdir()

        result = file_tool._run(operation="read", path="testdir")

        assert "错误" in result
        assert "不是文件" in result

    def test_list_file_as_directory(self, file_tool):
        """测试将文件当作目录列出"""
        # 创建文件
        file_tool._run(operation="write", path="test.txt", content="content")

        result = file_tool._run(operation="list", path="test.txt")

        assert "错误" in result
        assert "不是目录" in result

    @pytest.mark.asyncio
    async def test_async_run(self, file_tool):
        """测试异步执行"""
        result = await file_tool._arun(
            operation="write",
            path="async_test.txt",
            content="async content"
        )

        assert "成功写入文件" in result
