"""
测试错误处理中间件
"""
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.error_handler import (
    AppException,
    ErrorCode,
    register_exception_handlers
)


# 创建测试应用
app = FastAPI()

# 注册异常处理器
register_exception_handlers(app)


# 测试路由
@app.get("/test/app-exception")
async def test_app_exception():
    """测试AppException"""
    raise AppException(
        error_code=ErrorCode.USER_NOT_FOUND,
        message="用户不存在",
        status_code=404,
        details={"user_id": 123}
    )


@app.get("/test/validation-error")
async def test_validation_error(user_id: int):
    """测试验证错误"""
    return {"user_id": user_id}


@app.get("/test/general-exception")
async def test_general_exception():
    """测试通用异常"""
    raise ValueError("这是一个未捕获的异常")


@app.get("/test/success")
async def test_success():
    """测试成功响应"""
    return {"message": "成功"}


# 创建测试客户端（不抛出服务器异常）
client = TestClient(app, raise_server_exceptions=False)


def test_app_exception_handler():
    """测试AppException处理"""
    print("\n测试 AppException 处理...")
    response = client.get("/test/app-exception")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == ErrorCode.USER_NOT_FOUND.value
    assert data["message"] == "用户不存在"
    assert "details" in data
    assert data["details"]["user_id"] == 123
    print("✓ AppException 处理测试通过")


def test_validation_error_handler():
    """测试验证错误处理"""
    print("\n测试验证错误处理...")
    response = client.get("/test/validation-error?user_id=invalid")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == ErrorCode.VALIDATION_ERROR.value
    assert "details" in data
    assert "errors" in data["details"]
    print("✓ 验证错误处理测试通过")


def test_general_exception_handler():
    """测试通用异常处理"""
    print("\n测试通用异常处理...")
    response = client.get("/test/general-exception")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    assert response.status_code == 500
    data = response.json()
    assert data["error_code"] == ErrorCode.INTERNAL_SERVER_ERROR.value
    assert "服务器内部错误" in data["message"]
    print("✓ 通用异常处理测试通过")


def test_success_response():
    """测试正常响应"""
    print("\n测试正常响应...")
    response = client.get("/test/success")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "成功"
    print("✓ 正常响应测试通过")


def test_error_code_enum():
    """测试错误码枚举"""
    print("\n测试错误码枚举...")
    
    # 测试认证错误码
    assert ErrorCode.INVALID_CREDENTIALS.value == "1001"
    assert ErrorCode.TOKEN_EXPIRED.value == "1002"
    assert ErrorCode.USER_NOT_FOUND.value == "1004"
    
    # 测试业务错误码
    assert ErrorCode.CONVERSATION_NOT_FOUND.value == "2001"
    assert ErrorCode.DOCUMENT_UPLOAD_FAILED.value == "2004"
    assert ErrorCode.QUOTA_EXCEEDED.value == "2009"
    
    # 测试系统错误码
    assert ErrorCode.DATABASE_ERROR.value == "3001"
    assert ErrorCode.LLM_API_ERROR.value == "3004"
    
    # 测试权限错误码
    assert ErrorCode.RESOURCE_NOT_OWNED.value == "4001"
    
    # 测试验证错误码
    assert ErrorCode.VALIDATION_ERROR.value == "5001"
    
    print("✓ 错误码枚举测试通过")


def test_app_exception_to_dict():
    """测试AppException.to_dict方法"""
    print("\n测试 AppException.to_dict 方法...")
    
    exc = AppException(
        error_code=ErrorCode.USER_NOT_FOUND,
        message="用户不存在",
        status_code=404,
        details={"user_id": 123}
    )
    
    # 不带request_id
    result = exc.to_dict()
    assert result["error_code"] == ErrorCode.USER_NOT_FOUND.value
    assert result["message"] == "用户不存在"
    assert result["status_code"] == 404
    assert result["details"]["user_id"] == 123
    assert "request_id" not in result
    
    # 带request_id
    result_with_id = exc.to_dict(request_id="test-request-123")
    assert result_with_id["request_id"] == "test-request-123"
    
    print("✓ AppException.to_dict 方法测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("开始测试错误处理中间件")
    print("=" * 60)
    
    try:
        test_error_code_enum()
        test_app_exception_to_dict()
        test_app_exception_handler()
        test_validation_error_handler()
        test_general_exception_handler()
        test_success_response()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        raise
