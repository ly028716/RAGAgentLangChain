"""文件操作工具 - 用于文件系统操作"""
from pathlib import Path
from typing import Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class FileOperationsInput(BaseModel):
    """文件操作工具的输入模型"""

    operation: str = Field(
        description="要执行的操作类型: 'read'(读取文件), 'write'(写入文件), 'list'(列出目录), 'exists'(检查文件是否存在)"
    )
    path: str = Field(description="文件或目录的路径")
    content: Optional[str] = Field(default=None, description="写入操作时的文件内容")


class FileOperationsTool(BaseTool):
    """
    文件操作工具 - 执行基本的文件系统操作

    支持的操作:
    - read: 读取文件内容
    - write: 写入文件内容
    - list: 列出目录中的文件
    - exists: 检查文件或目录是否存在

    安全限制:
    - 只能在指定的工作目录内操作
    - 不能访问系统敏感目录
    """

    name: str = "file_operations"
    description: str = (
        "用于执行文件系统操作的工具。"
        "支持读取文件(read)、写入文件(write)、列出目录(list)、检查文件存在(exists)。"
        "示例: operation='read', path='data.txt' 或 operation='write', path='output.txt', content='Hello'"
    )
    args_schema: Type[BaseModel] = FileOperationsInput
    base_path: str = "./workspace"  # 工作目录，限制操作范围

    def _is_safe_path(self, path: str) -> bool:
        """
        检查路径是否安全（在允许的工作目录内）

        Args:
            path: 要检查的路径

        Returns:
            如果路径安全返回True，否则返回False
        """
        try:
            # 确保base_path存在
            base = Path(self.base_path).resolve()
            target = (base / path).resolve()

            # 检查目标路径是否在base_path内
            return str(target).startswith(str(base))
        except Exception:
            return False

    def _read_file(self, path: str) -> str:
        """读取文件内容"""
        full_path = Path(self.base_path) / path

        if not full_path.exists():
            return f"错误: 文件不存在: {path}"

        if not full_path.is_file():
            return f"错误: 路径不是文件: {path}"

        # 检查文件大小
        file_size = full_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return f"错误: 文件过大 ({file_size / 1024 / 1024:.2f}MB)，最大支持 {max_size / 1024 / 1024}MB"

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"文件内容:\n{content}"
        except Exception as e:
            return f"读取文件失败: {str(e)}"

    def _write_file(self, path: str, content: str) -> str:
        """写入文件内容"""
        full_path = Path(self.base_path) / path

        try:
            # 确保父目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"成功写入文件: {path}"
        except Exception as e:
            return f"写入文件失败: {str(e)}"

    def _list_directory(self, path: str) -> str:
        """列出目录内容"""
        full_path = Path(self.base_path) / path

        if not full_path.exists():
            return f"错误: 目录不存在: {path}"

        if not full_path.is_dir():
            return f"错误: 路径不是目录: {path}"

        try:
            items = []
            for item in full_path.iterdir():
                item_type = "目录" if item.is_dir() else "文件"
                items.append(f"- {item.name} ({item_type})")

            if not items:
                return f"目录为空: {path}"

            return f"目录内容:\n" + "\n".join(items)
        except Exception as e:
            return f"列出目录失败: {str(e)}"

    def _check_exists(self, path: str) -> str:
        """检查文件或目录是否存在"""
        full_path = Path(self.base_path) / path

        if full_path.exists():
            item_type = "目录" if full_path.is_dir() else "文件"
            return f"存在: {path} ({item_type})"
        else:
            return f"不存在: {path}"

    def _run(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        执行文件操作

        Args:
            operation: 操作类型
            path: 文件或目录路径
            content: 写入操作时的内容
            run_manager: 回调管理器

        Returns:
            操作结果的字符串表示
        """
        try:
            # 确保工作目录存在
            Path(self.base_path).mkdir(parents=True, exist_ok=True)

            # 检查路径安全性
            if not self._is_safe_path(path):
                return f"错误: 不允许访问路径: {path}"

            # 执行对应的操作
            if operation == "read":
                return self._read_file(path)
            elif operation == "write":
                if content is None:
                    return "错误: 写入操作需要提供content参数"
                return self._write_file(path, content)
            elif operation == "list":
                return self._list_directory(path)
            elif operation == "exists":
                return self._check_exists(path)
            else:
                return f"错误: 不支持的操作类型: {operation}"

        except Exception as e:
            return f"文件操作失败: {str(e)}"

    async def _arun(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """异步执行文件操作（实际上调用同步方法）"""
        return self._run(operation, path, content, run_manager)
