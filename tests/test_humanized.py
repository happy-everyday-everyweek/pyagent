"""
PyAgent 拟人化系统测试
"""

import pytest

from src.interaction.heart_flow import (
    ActionType,
    BehaviorPlanner,
    ConversationContext,
    ConversationGoal,
    EmotionType,
    HumanizedPromptBuilder,
)


class TestHumanizedPromptBuilder:
    """拟人化Prompt构建器测试"""

    def test_create_builder(self):
        """测试创建构建器"""
        builder = HumanizedPromptBuilder()
        assert builder is not None

    def test_get_persona_text(self):
        """测试获取人设文本"""
        builder = HumanizedPromptBuilder(config={"bot_name": "测试助手"})
        persona = builder.get_persona_text()
        
        assert "测试助手" in persona

    def test_build_direct_reply_prompt(self):
        """测试构建直接回复Prompt"""
        builder = HumanizedPromptBuilder()
        
        prompt = builder.build_direct_reply_prompt(
            chat_history="用户: 你好\n助手: 你好",
            goals=[ConversationGoal(goal="测试目标", reasoning="测试原因")],
        )
        
        assert "回复" in prompt
        assert "测试目标" in prompt

    def test_build_follow_up_prompt(self):
        """测试构建追问Prompt"""
        builder = HumanizedPromptBuilder()
        
        prompt = builder.build_follow_up_prompt(
            chat_history="用户: 你好\n助手: 你好",
            last_reply="你好",
        )
        
        assert "新消息" in prompt

    def test_build_goodbye_prompt(self):
        """测试构建告别语Prompt"""
        builder = HumanizedPromptBuilder()
        
        prompt = builder.build_goodbye_prompt(
            chat_history="用户: 再见\n助手: 好的",
        )
        
        assert "告别" in prompt or "结束" in prompt

    def test_update_emotion(self):
        """测试更新情感"""
        builder = HumanizedPromptBuilder()
        
        builder.update_emotion(messages=[{"content": "谢谢你的帮助，我很开心"}])
        
        assert builder._emotion_state.emotion_type == EmotionType.HAPPY

    def test_get_status(self):
        """测试获取状态"""
        builder = HumanizedPromptBuilder(config={"bot_name": "测试助手"})
        
        status = builder.get_status()
        
        assert status["bot_name"] == "测试助手"
        assert "emotion" in status


class TestBehaviorPlanner:
    """行为规划器测试"""

    def test_create_planner(self):
        """测试创建规划器"""
        planner = BehaviorPlanner()
        assert planner is not None

    def test_should_greet(self):
        """测试问候判断"""
        planner = BehaviorPlanner()
        
        should_greet, greeting_type = planner.should_greet()
        
        assert isinstance(should_greet, bool)
        if should_greet:
            assert greeting_type in ["morning", "noon", "afternoon", "evening", "night"]

    def test_get_greeting_message(self):
        """测试获取问候消息"""
        planner = BehaviorPlanner()
        
        message = planner.get_greeting_message("morning")
        
        assert message in ["早安", "早上好", "早啊"]

    def test_plan_action(self):
        """测试规划行动"""
        planner = BehaviorPlanner()
        context = ConversationContext()
        
        decision = planner.plan_action(context, is_at=True)
        
        assert decision.action == ActionType.DIRECT_REPLY
        assert decision.confidence > 0

    def test_should_end_conversation(self):
        """测试结束对话判断"""
        planner = BehaviorPlanner()
        context = ConversationContext()
        
        result = planner.should_end_conversation(
            context=context,
            last_messages=["再见"],
        )
        
        assert result

    def test_get_end_conversation_message(self):
        """测试获取结束对话消息"""
        planner = BehaviorPlanner()
        
        message = planner.get_end_conversation_message()
        
        assert len(message) > 0
