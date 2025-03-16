from PySide6.QtWidgets import QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from chat_logic import ChatLogic

class ChatInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat with Ai")
        self.resize(500, 400)

        ui_file = QFile("ui/chat_interface.ui")
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file)
        ui_file.close()
        self.setCentralWidget(self.ui)

        self.chat_logic = ChatLogic()

        self.chat_display = self.ui.findChild(QTextEdit, "chatDisplay")
        self.user_input_entry = self.ui.findChild(QLineEdit, "userInputEntry")
        self.send_button = self.ui.findChild(QPushButton, "sendButton")
        self.exit_button = self.ui.findChild(QPushButton, "exitButton")

        self.send_button.clicked.connect(self.send_message)
        self.exit_button.clicked.connect(self.close)

    def send_message(self):
        user_input = self.user_input_entry.text()
        if not user_input.strip():
            return

        self.chat_display.append(f"You: {user_input}")

        ai_reply = self.chat_logic.send_message(user_input)
        if ai_reply:
            self.chat_display.append(f"Ai: {ai_reply}\n")

        self.user_input_entry.clear()