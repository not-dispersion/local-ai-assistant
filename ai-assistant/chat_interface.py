from PySide6.QtWidgets import (QMainWindow, QTextEdit, QLineEdit, QPushButton, 
                              QVBoxLayout, QWidget, QMessageBox, QFileDialog)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from chat_logic import ChatLogic

class ChatInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat with Ai")
        self.resize(500, 450)

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
        self.file_mode_button = self.ui.findChild(QPushButton, "fileModeButton")
        self.change_folder_button = self.ui.findChild(QPushButton, "changeFolderButton")
        self.web_search_button = self.ui.findChild(QPushButton, "webSearchButton")

        self.send_button.clicked.connect(self.send_message)
        self.exit_button.clicked.connect(self.close)
        self.file_mode_button.clicked.connect(self.toggle_file_mode)
        self.change_folder_button.clicked.connect(self.prompt_local_folder)
        self.web_search_button.clicked.connect(self.toggle_web_search)

        self.file_mode_button.setCheckable(True)
        self.file_mode_button.setText("Enable File Mode")
        self.web_search_button.setCheckable(True)
        self.web_search_button.setText("Enable Web Search")

        if not self.chat_logic.file_handler.local_folder:
            self.prompt_local_folder()

    def prompt_local_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Local Folder")
        if folder_path:
            self.chat_logic.file_handler.save_local_folder(folder_path)
            QMessageBox.information(self, "Success", f"Local folder set to: {folder_path}")
        else:
            QMessageBox.warning(self, "Warning", "Local folder is required for file mode.")

    def toggle_file_mode(self):
        enabled = self.file_mode_button.isChecked()
        message = self.chat_logic.toggle_file_mode(enabled)
        if message:
            QMessageBox.information(self, "Information", message)
        self.file_mode_button.setText("Disable File Mode" if enabled else "Enable File Mode")

    def toggle_web_search(self):
        enabled = self.web_search_button.isChecked()
        self.chat_logic.web_search_handler.toggle_enabled(enabled)
        self.web_search_button.setText("Disable Web Search" if enabled else "Enable Web Search")

    def send_message(self):
        user_input = self.user_input_entry.text()
        if not user_input.strip():
            return

        self.chat_display.append(f"You: {user_input}")

        ai_reply = self.chat_logic.send_message(user_input)
        if ai_reply:
            self.chat_display.append(f"Ai: {ai_reply}\n")

        self.user_input_entry.clear()
        
    def closeEvent(self, event):
        try:
            self.chat_logic.finalize()
            event.accept()
        except Exception as e:
            print(f"Error on close: {str(e)}")
            event.accept()
