import unittest
from unittest.mock import MagicMock
from interfaces import IBotCommand, CommandResult
from bot import CodeAssistantBot


class TestCodeAssistantBot(unittest.TestCase):

    def setUp(self):
        """Inicializa una nueva instancia del bot antes de cada prueba."""
        self.bot = CodeAssistantBot("DevSentinelTest")
        
        # Mock de un comando para reutilizar en las pruebas
        self.mock_command = MagicMock(spec=IBotCommand)
        self.mock_command.name = "test_cmd"

    def test_init_default_name(self):
        """Verifica que el bot tome el nombre por defecto si no se pasa argumento."""
        default_bot = CodeAssistantBot()
        self.assertEqual(default_bot.bot_name, "DevSentinel")

    def test_init_custom_name(self):
        """Verifica la asignación de un nombre personalizado."""
        self.assertEqual(self.bot.bot_name, "DevSentinelTest")

    def test_register_command(self):
        """Verifica que los comandos se registren correctamente en el diccionario interno."""
        self.bot.register_command(self.mock_command)
        self.assertIn("test_cmd", self.bot._registry)
        self.assertEqual(self.bot._registry["test_cmd"], self.mock_command)

    def test_process_request_unregistered_command(self):
        """Verifica la respuesta de error al ejecutar un comando no registrado."""
        result = self.bot.process_request("cmd_inexistente", payload={})
        
        self.assertFalse(result.success)
        self.assertEqual(result.output, "Comando 'cmd_inexistente' no registrado.")

    def test_process_request_success(self):
        """Verifica que un comando registrado se ejecute y retorne el resultado esperado."""
        expected_result = CommandResult(success=True, output="Éxito")
        self.mock_command.execute.return_value = expected_result

        self.bot.register_command(self.mock_command)
        
        payload = {"data": 123}
        result = self.bot.process_request("test_cmd", payload)

        # Verificaciones de retorno e invocación del comando
        self.assertEqual(result, expected_result)
        self.mock_command.execute.assert_called_once_with(payload)

    def test_process_request_with_kwargs(self):
        """Verifica que se transmitan argumentos nombrados adicionales (kwargs)."""
        expected_result = CommandResult(success=True, output="Ok con kwargs")
        self.mock_command.execute.return_value = expected_result

        self.bot.register_command(self.mock_command)
        
        payload = {"game_id": "123"}
        self.bot.process_request("test_cmd", payload, extra_param=True, debug=False)

        # Revisa que kwargs haya llegado completo al método execute
        self.mock_command.execute.assert_called_once_with(
            payload, extra_param=True, debug=False
        )


if __name__ == "__main__":
    unittest.main()