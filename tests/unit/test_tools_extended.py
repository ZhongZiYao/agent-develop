"""工具扩展测试

测试新增的 web_search 和 code_execution 工具
"""

import pytest

from src.agents.tools import code_execution_tool, web_search_tool


class TestWebSearch:
    """测试 Web 搜索工具"""

    @pytest.mark.asyncio
    async def test_basic_web_search(self):
        """测试基础搜索"""
        results = await web_search_tool("妖刀姬 S13 改动", num_results=3)

        assert isinstance(results, list)
        assert len(results) == 3

        for result in results:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result

        print(f"\n✅ Web search works")
        print(f"   Results: {len(results)}")
        print(f"   Example: {results[0]['title']}")

    @pytest.mark.asyncio
    async def test_web_search_with_limit(self):
        """测试限制结果数量"""
        results = await web_search_tool("阴阳师攻略", num_results=5)

        assert len(results) == 5

        print(f"\n✅ Web search limit works")
        print(f"   Requested: 5, Got: {len(results)}")


class TestCodeExecution:
    """测试代码执行工具"""

    @pytest.mark.asyncio
    async def test_simple_calculation(self):
        """测试简单计算"""
        code = "print(1.2 * 100)"
        result = await code_execution_tool(code)

        assert result["success"] is True
        assert "120" in result["output"]
        assert result["error"] is None

        print(f"\n✅ Simple calculation works")
        print(f"   Code: {code}")
        print(f"   Output: {result['output'].strip()}")

    @pytest.mark.asyncio
    async def test_complex_calculation(self):
        """测试复杂计算"""
        code = """
damage_base = 100
damage_coefficient = 1.2
crit_rate = 0.3
crit_damage = 1.5

normal_damage = damage_base * damage_coefficient
crit_final = normal_damage * crit_damage
expected_damage = normal_damage * (1 - crit_rate) + crit_final * crit_rate

print(f"期望伤害: {expected_damage}")
"""
        result = await code_execution_tool(code)

        assert result["success"] is True
        assert "期望伤害" in result["output"]
        assert result["error"] is None

        print(f"\n✅ Complex calculation works")
        print(f"   Output: {result['output'].strip()}")

    @pytest.mark.asyncio
    async def test_list_operations(self):
        """测试列表操作"""
        code = """
damages = [100, 120, 150, 130, 110]
avg_damage = sum(damages) / len(damages)
max_damage = max(damages)
min_damage = min(damages)

print(f"平均伤害: {avg_damage}")
print(f"最高伤害: {max_damage}")
print(f"最低伤害: {min_damage}")
"""
        result = await code_execution_tool(code)

        assert result["success"] is True
        assert "平均伤害" in result["output"]
        assert result["error"] is None

        print(f"\n✅ List operations work")
        print(f"   Output:\n{result['output']}")

    @pytest.mark.asyncio
    async def test_code_execution_error(self):
        """测试错误处理"""
        code = "print(undefined_variable)"
        result = await code_execution_tool(code)

        assert result["success"] is False
        assert result["error"] is not None
        assert "undefined_variable" in result["error"]

        print(f"\n✅ Error handling works")
        print(f"   Error: {result['error']}")

    @pytest.mark.asyncio
    async def test_unsafe_operations_blocked(self):
        """测试危险操作被阻止"""
        # 尝试访问文件系统（应该失败）
        code = "import os; print(os.listdir())"
        result = await code_execution_tool(code)

        assert result["success"] is False
        # import 被阻止

        print(f"\n✅ Unsafe operations blocked")
        print(f"   Error: {result['error']}")

    @pytest.mark.asyncio
    async def test_damage_calculator(self):
        """测试伤害计算器（实际用例）"""
        code = """
# 妖刀姬振刀伤害计算
base_damage = 100
skill_coefficient = 1.2
attack_bonus = 50

final_damage = (base_damage + attack_bonus) * skill_coefficient
print(f"振刀伤害: {final_damage}")
"""
        result = await code_execution_tool(code)

        assert result["success"] is True
        assert "180" in result["output"]

        print(f"\n✅ Damage calculator works")
        print(f"   Output: {result['output'].strip()}")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
