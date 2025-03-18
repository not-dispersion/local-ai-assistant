import os
import json
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import ollama

class ChatLogic:
    def __init__(self):
        self.log_file = "chat_log.jsonl"
        self.current_conversation = []
        self.system_prompt = {
            "role": "system",
            "content": (
                "Ты ИИ по имени Ай. Поддерживай естественный диалог без повторных приветствий. "
                "Используй русский язык и кириллицу. Отвечай как дружелюбный помощник, "
                "учитывая контекст текущего и предыдущих разговоров."
            )
        }
        self._init_conversation()
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not os.path.exists(self.log_file):
            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    pass
            except Exception as e:
                print(f"Failed to create log file: {str(e)}")

    def _init_conversation(self):
        if not any(isinstance(msg, dict) and msg.get("role") == "system" 
                   for msg in self.current_conversation):
            self.current_conversation.append(self.system_prompt)

    def load_chat_log(self):
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as file:
                return [
                    json.loads(line) for line in file 
                    if line.strip() and "conversation" in json.loads(line)
                ]
        except Exception as e:
            print(f"Error loading chat log: {str(e)}")
            return []

    def get_embedding(self, text):
        try:
            response = ollama.embeddings(model='nomic-embed-text', prompt=text)
            return response['embedding']
        except Exception as e:
            print(f"Embedding error: {str(e)}")
            return []

    def find_relevant_context(self, user_input):
        try:
            user_embedding = self.get_embedding(user_input)
            if not user_embedding:
                return []

            all_matches = []
            chat_log = self.load_chat_log()

            for entry in chat_log:
                if not isinstance(entry, dict) or "conversation" not in entry:
                    continue

                conversation = entry.get("conversation", [])
                for i, message in enumerate(conversation):
                    if not isinstance(message, dict) or message.get("role") != "user":
                        continue

                    content = message.get("content", "")
                    if not content:
                        continue

                    embedding = message.get("embedding", self.get_embedding(content))
                    if not embedding:
                        continue

                    try:
                        similarity = cosine_similarity([user_embedding], [embedding])[0][0]
                    except ValueError:
                        continue

                    assistant_response = next(
                        (m.get("content", "") for m in conversation[i+1:] 
                         if isinstance(m, dict) and m.get("role") == "assistant"),
                        ""
                    )

                    all_matches.append({
                        "content": content,
                        "response": assistant_response,
                        "similarity": similarity
                    })

            filtered = sorted(
                [m for m in all_matches if m["similarity"] > 0.55],
                key=lambda x: x["similarity"], 
                reverse=True
            )[:3]
            
            return [
                f"- Ранее: '{self._truncate(m['content'], 75)}' → "
                f"Ответ: '{self._truncate(m['response'], 100)}'"
                for m in filtered
            ]
        
        except Exception as e:
            print(f"Context error: {str(e)}")
            return []

    def _truncate(self, text, length):
        return (text[:length] + "...") if len(text) > length else text

    def send_message(self, user_input):
        try:
            if not user_input.strip():
                return None

            self.current_conversation.append({
                "role": "user",
                "content": user_input,
                "embedding": self.get_embedding(user_input)
            })

            messages = [msg.copy() for msg in self.current_conversation 
                        if isinstance(msg, dict)]
            
            if context := self.find_relevant_context(user_input):
                messages.insert(1, {
                    "role": "system",
                    "content": "Контекст из истории:\n" + "\n".join(context)
                })

            response = ollama.chat(model="llama3", messages=messages[-6:])
            ai_reply = response['message']['content']
            
            self.current_conversation.append({
                "role": "assistant",
                "content": ai_reply,
                "embedding": self.get_embedding(ai_reply)  # Сохранение эмбеддинга
            })

            self.save_conversation()
            return ai_reply
        
        except Exception as e:
            print(f"Processing error: {str(e)}")
            return "Извините, произошла ошибка. Попробуйте еще раз."

    def save_conversation(self):
        try:
            if len(self.current_conversation) >= 2:
                useful_messages = [
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "embedding": msg["embedding"]  # Теперь сохраняем эмбеддинг для всех сообщений
                    }
                    for msg in self.current_conversation
                    if isinstance(msg, dict) 
                    and msg["role"] in ("user", "assistant")
                    and msg.get("content")
                ]

                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "conversation": useful_messages
                }

                with open(self.log_file, "a", encoding="utf-8") as file:
                    file.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
                self.current_conversation = [
                    msg for msg in self.current_conversation 
                    if isinstance(msg, dict) 
                    and msg.get("role") == "system"
                ]

        except Exception as e:
            print(f"Saving error: {str(e)}")
            with open("chat_log_backup.txt", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] Backup: {str(self.current_conversation)}\n")
