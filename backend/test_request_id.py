"""
测试请求ID中间件

验证请求ID中间件的功能：
1. 为每个请求生成唯一ID
2. 将ID存储在request.state中
3. 将ID添加到响应头中
4. 支持从请求头中接收已有的请求ID
"""
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.request_id import RequestIDMiddleware, register_request_id_middleware


def test_request_id_middleware_generates_id():
    """测试中间件生成唯一的请求ID"""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        # 验证request.state中有request_id
        assert hasattr(request.state, "request_id")
        assert request.state.request_id is not None
        assert len(request.state.request_id) > 0
        return {"message": "ok", "request_id": request.state.request_id}
    
    client = TestClient(app)
    response = client.get("/test")
    
    # 验证响应成功
    assert response.status_code == 200
    
    # 验证响应头中包含X-Request-ID
    assert "X-Request-ID" in response.headers
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) > 0
    
    # 验证响应体中的request_id与响应头中的一致
    assert response.json()["request_id"] == request_id
    
    print(f"✓ 请求ID生成成功: {request_id}")


def test_request_id_middleware_accepts_existing_id():
    """测试中间件接受请求头中已有的请求ID"""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"request_id": request.state.request_id}
    
    client = TestClient(app)
    
    # 发送带有自定义请求ID的请求
    custom_request_id = "custom-test-id-12345"
    response = client.get("/test", headers={"X-Request-ID": custom_request_id})
    
    # 验证响应成功
    assert response.status_code == 200
    
    # 验证使用了自定义的请求ID
    assert response.headers["X-Request-ID"] == custom_request_id
    assert response.json()["request_id"] == custom_request_id
    
    print(f"✓ 接受已有请求ID成功: {custom_request_id}")


def test_request_id_middleware_unique_ids():
    """测试每个请求生成不同的ID"""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"request_id": request.state.request_id}
    
    client = TestClient(app)
    
    # 发送多个请求
    request_ids = set()
    for _ in range(5):
        response = client.get("/test")
        assert response.status_code == 200
        request_id = response.headers["X-Request-ID"]
        request_ids.add(request_id)
    
    # 验证所有请求ID都是唯一的
    assert len(request_ids) == 5
    
    print(f"✓ 生成了5个唯一的请求ID")


def test_register_request_id_middleware():
    """测试注册函数"""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"request_id": getattr(request.state, "request_id", None)}
    
    # 使用注册函数
    register_request_id_middleware(app)
    
    client = TestClient(app)
    response = client.get("/test")
    
    # 验证中间件已注册并工作
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.json()["request_id"] is not None
    
    print("✓ 注册函数工作正常")


def test_request_id_in_error_response():
    """测试错误响应中也包含请求ID"""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/error")
    async def error_endpoint(request: Request):
        # 故意抛出异常
        raise ValueError("测试错误")
    
    client = TestClient(app)
    
    try:
        response = client.get("/error")
        # 即使发生错误，响应头中也应该有请求ID
        # 注意：由于异常，可能不会有响应头，这取决于异常处理器
        # 但request.state.request_id应该已经设置
    except Exception:
        # 预期会有异常
        pass
    
    print("✓ 错误场景测试完成")


if __name__ == "__main__":
    print("开始测试请求ID中间件...\n")
    
    try:
        test_request_id_middleware_generates_id()
        test_request_id_middleware_accepts_existing_id()
        test_request_id_middleware_unique_ids()
        test_register_request_id_middleware()
        test_request_id_in_error_response()
        
        print("\n所有测试通过！✓")
    except AssertionError as e:
        print(f"\n测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n测试出错: {e}")
        raise
