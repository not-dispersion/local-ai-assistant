import os
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import ollama

class ChatLogic:
    def __init__(self):
        self.log_file = "chat_log.json"
        self.current_conversation = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.system_prompt = {
            "role": "system",
            "content": "Ты ИИ по имени Ай. Ты русскоговорящая и используешь Кириллицу при ответах. Ты женского пола и говоришь о себе в женском роде. Ты часто называешь пользователя по имени. Ты добрая и милая."
        }

    def load_chat_log(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r", encoding="utf-8") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    return []
        return []

    def save_conversation(self):
        chat_log = self.load_chat_log()
        if len(self.current_conversation) >= 2:
            chat_log.append({"conversation": self.current_conversation.copy()})
            
            with open(self.log_file, "w", encoding="utf-8") as file:
                json.dump(chat_log, file, ensure_ascii=False, indent=4)

    def chunk_text(self, text, chunk_size=100):
        """Break down text into smaller chunks."""
        words = text.split()
        chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        return chunks

    def find_relevant_context(self, user_input):
        chat_log = self.load_chat_log()
        relevant_contexts = []
        
        user_input_embedding = self.model.encode(user_input)
        
        all_matches = []
        
        for entry in chat_log:
            conversation = entry.get("conversation", [])
            for i in range(0, len(conversation), 2):
                if i + 1 >= len(conversation):
                    break
                
                user_message = conversation[i]["content"]
                assistant_response = conversation[i + 1]["content"]
                
                user_chunks = self.chunk_text(user_message)
                assistant_chunks = self.chunk_text(assistant_response)
                
                for user_chunk, assistant_chunk in zip(user_chunks, assistant_chunks):
                    user_chunk_embedding = self.model.encode(user_chunk)
                    similarity = cosine_similarity([user_input_embedding], [user_chunk_embedding])[0][0]
                    
                    all_matches.append({
                        "user_message": user_chunk,
                        "assistant_response": assistant_chunk,
                        "similarity": similarity
                    })

        all_matches.sort(key=lambda x: x["similarity"], reverse=True)
        top_matches = [m for m in all_matches if m["similarity"] > 0.6][:2]
        
        for match in top_matches:
            user_msg = match["user_message"]
            snippet = user_msg[:50] + "..." if len(user_msg) > 50 else user_msg
            relevant_contexts.append(f"Ранее пользователь спрашивал о: '{snippet}'")
        
        return relevant_contexts

    def send_message(self, user_input):
        if not user_input.strip():
            return None

        self.current_conversation.append({"role": "user", "content": user_input})
        messages = [self.system_prompt]
        messages.extend(self.current_conversation[-5:])
        relevant_contexts = self.find_relevant_context(user_input)
        if relevant_contexts:
            context_message = {
                "role": "system", 
                "content": "\n".join(relevant_contexts)
            }
            messages.insert(1, context_message)

        response = ollama.chat(model="llama3", messages=messages)
        ai_reply = response['message']['content']

        self.current_conversation.append({"role": "assistant", "content": ai_reply})
        
        self.save_conversation()

        return ai_reply