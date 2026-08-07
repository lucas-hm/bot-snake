import unittest
from bot import CodeAssistantBot
from game_engine import GameMoveTool

class TestDevSentinelIntegrations(unittest.TestCase):

    def setUp(self):
        self.bot = CodeAssistantBot("DevSentinel")
        self.bot.register_command(GameMoveTool())

    def test_move_calculation_returns_valid_payload(self):
        sample_turn_data = {
            "game_id": "game_123",
            "turn_token": "token_abc",
            "board": "|---|---|---|"
        }
        result = self.bot.process_request("calculate_move", sample_turn_data)
        
        self.assertTrue(result.success)
        self.assertEqual(result.output["game_id"], "game_123")
        self.assertEqual(result.output["turn_token"], "token_abc")
        self.assertIn("col", result.output)

if __name__ == "__main__":
    unittest.main()