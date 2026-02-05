"""计算器工具 - 用于数学计算"""
import ast
import math
import operator
from typing import Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    """计算器工具的输入模型"""

    expression: str = Field(description="要计算的数学表达式，例如: '2 + 2', '10 * 5', 'sqrt(16)'")


class CalculatorTool(BaseTool):
    """
    计算器工具 - 执行基本的数学计算

    支持的操作:
    - 基本运算: +, -, *, /, //, %, **
    - 数学函数: sqrt, sin, cos, tan, log, exp, abs
    - 常量: pi, e
    """

    name: str = "calculator"
    description: str = (
        "用于执行数学计算的工具。"
        "输入应该是一个有效的数学表达式，例如: '2 + 2', '10 * 5', 'sqrt(16)', 'sin(pi/2)'。"
        "支持基本运算符(+, -, *, /, **, %)和常用数学函数(sqrt, sin, cos, tan, log, exp, abs)。"
    )
    args_schema: Type[BaseModel] = CalculatorInput

    # 安全的操作符和函数白名单
    _safe_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    _safe_functions = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
    }

    _safe_constants = {
        "pi": math.pi,
        "e": math.e,
    }

    def _eval_node(self, node):
        """安全地评估AST节点"""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type not in self._safe_operators:
                raise ValueError(f"不支持的操作符: {op_type.__name__}")
            return self._safe_operators[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in self._safe_operators:
                raise ValueError(f"不支持的一元操作符: {op_type.__name__}")
            return self._safe_operators[op_type](operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name not in self._safe_functions:
                raise ValueError(f"不支持的函数: {func_name}")
            args = [self._eval_node(arg) for arg in node.args]
            return self._safe_functions[func_name](*args)
        elif isinstance(node, ast.Name):
            if node.id in self._safe_constants:
                return self._safe_constants[node.id]
            raise ValueError(f"未定义的变量: {node.id}")
        else:
            raise ValueError(f"不支持的表达式类型: {type(node).__name__}")

    def _safe_eval(self, expression: str) -> float:
        """
        安全地评估数学表达式

        Args:
            expression: 数学表达式字符串

        Returns:
            计算结果

        Raises:
            ValueError: 如果表达式无效或包含不安全的操作
        """
        try:
            # 解析表达式为AST
            tree = ast.parse(expression, mode="eval")

            # 评估AST
            result = self._eval_node(tree.body)

            return result
        except SyntaxError as e:
            raise ValueError(f"语法错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"计算错误: {str(e)}")

    def _run(
        self,
        expression: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        执行计算

        Args:
            expression: 要计算的数学表达式
            run_manager: 回调管理器

        Returns:
            计算结果的字符串表示
        """
        try:
            # 清理表达式（移除空格）
            expression = expression.strip()

            if not expression:
                return "错误: 表达式不能为空"

            # 执行计算
            result = self._safe_eval(expression)

            # 格式化结果
            if isinstance(result, float):
                # 如果是整数结果，不显示小数点
                if result.is_integer():
                    return str(int(result))
                # 否则保留合理的小数位数
                return f"{result:.10g}"

            return str(result)

        except ValueError as e:
            return f"错误: {str(e)}"
        except ZeroDivisionError:
            return "错误: 除数不能为零"
        except Exception as e:
            return f"计算失败: {str(e)}"

    async def _arun(
        self,
        expression: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """异步执行计算（实际上调用同步方法）"""
        return self._run(expression, run_manager)
