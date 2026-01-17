"""
测试对话导出和标题生成功能

验证需求2.6和需求2.8的实现。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_service import ConversationService
from app.models.message import MessageRole
from app.core.database import SessionLocal


def test_export_conversation():
    """测试对话导出功能"""
    print("\n=== 测试对话导出功能 ===")
    
    db = SessionLocal()
    try:
        service = ConversationService(db)
        
        # 创建测试对话
        conversation = service.create_conversation(
            user_id=1,
            title="测试对话"
        )
        print(f"✓ 创建测试对话: ID={conversation.id}")
        
        # 添加测试消息
        service.add_message(
            conversation_id=conversation.id,
            user_id=1,
            role=MessageRole.USER,
            content="你好，请介绍一下Python",
            tokens=0
        )
        
        service.add_message(
            conversation_id=conversation.id,
            user_id=1,
            role=MessageRole.ASSISTANT,
            content="Python是一种高级编程语言，具有简洁的语法和强大的功能。",
            tokens=50
        )
        print("✓ 添加测试消息")
        
        # 测试Markdown导出
        print("\n--- 测试Markdown导出 ---")
        markdown_content = service.export_conversation(
            conversation_id=conversation.id,
            user_id=1,
            format="markdown"
        )
        print("✓ Markdown导出成功")
        print(f"导出内容长度: {len(markdown_content)} 字符")
        print("\n导出内容预览:")
        print(markdown_content[:500])
        
        # 测试JSON导出
        print("\n--- 测试JSON导出 ---")
        json_content = service.export_conversation(
            conversation_id=conversation.id,
            user_id=1,
            format="json"
        )
        print("✓ JSON导出成功")
        print(f"导出内容长度: {len(json_content)} 字符")
        print("\n导出内容预览:")
        print(json_content[:500])
        
        # 测试不支持的格式
        print("\n--- 测试不支持的格式 ---")
        try:
            service.export_conversation(
                conversation_id=conversation.id,
                user_id=1,
                format="xml"
            )
            print("✗ 应该抛出ValueError异常")
        except ValueError as e:
            print(f"✓ 正确抛出异常: {str(e)}")
        
        # 清理测试数据
        service.delete_conversation(conversation.id, 1)
        print("\n✓ 清理测试数据")
        
    finally:
        db.close()


def test_generate_title():
    """测试标题生成功能"""
    print("\n=== 测试标题生成功能 ===")
    
    db = SessionLocal()
    try:
        service = ConversationService(db)
        
        # 测试用例
        test_messages = [
            "你好，请介绍一下Python编程语言",
            "我想学习机器学习，应该从哪里开始？",
            "如何使用FastAPI构建RESTful API？",
            "请帮我写一个冒泡排序的Python代码",
        ]
        
        print("\n注意: 标题生成需要调用LLM API，如果API密钥未配置，将返回默认标题")
        print("如果看到'新对话'，说明API调用失败，但功能逻辑正确\n")
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- 测试用例 {i} ---")
            print(f"消息: {message}")
            
            try:
                # 使用同步版本进行测试
                title = service.generate_title_sync(
                    first_message=message,
                    max_length=20
                )
                print(f"✓ 生成标题: {title}")
                print(f"  标题长度: {len(title)} 字符")
                
                # 验证标题长度
                if len(title) <= 20:
                    print("  ✓ 标题长度符合要求")
                else:
                    print(f"  ✗ 标题长度超过限制: {len(title)} > 20")
                
            except Exception as e:
                print(f"✗ 标题生成失败: {str(e)}")
        
    finally:
        db.close()


def test_is_first_user_message():
    """测试检查是否为第一条用户消息"""
    print("\n=== 测试检查第一条用户消息 ===")
    
    db = SessionLocal()
    try:
        service = ConversationService(db)
        
        # 创建测试对话
        conversation = service.create_conversation(
            user_id=1,
            title="测试对话"
        )
        print(f"✓ 创建测试对话: ID={conversation.id}")
        
        # 检查空对话
        is_first = service.is_first_user_message(conversation.id)
        print(f"空对话检查: {is_first}")
        if is_first:
            print("✓ 空对话正确返回True")
        else:
            print("✗ 空对话应该返回True")
        
        # 添加第一条用户消息
        service.add_message(
            conversation_id=conversation.id,
            user_id=1,
            role=MessageRole.USER,
            content="第一条消息",
            tokens=0
        )
        
        # 再次检查
        is_first = service.is_first_user_message(conversation.id)
        print(f"有消息后检查: {is_first}")
        if not is_first:
            print("✓ 有消息后正确返回False")
        else:
            print("✗ 有消息后应该返回False")
        
        # 清理测试数据
        service.delete_conversation(conversation.id, 1)
        print("\n✓ 清理测试数据")
        
    finally:
        db.close()


def main():
    """运行所有测试"""
    print("=" * 60)
    print("对话导出和标题生成功能测试")
    print("=" * 60)
    
    try:
        # 测试导出功能
        test_export_conversation()
        
        # 测试第一条消息检查
        test_is_first_user_message()
        
        # 测试标题生成功能
        test_generate_title()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
