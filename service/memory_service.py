"""Memory Service - Quản lý lưu trữ hội thoại."""
from typing import Optional

from controller.interfaces import ISqlService


class MemoryService:
    def __init__(self, sql_service: ISqlService):
        self.sql = sql_service
        self.context_file = "database/user_memory.json"
        
    def _get_context_file_path(self):
        import os
        from pathlib import Path
        project_root = Path(__file__).resolve().parent.parent
        db_dir = project_root / "database"
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / "user_memory.json"
    
    def save_exchange(self, user_name: str, user_msg: str, 
                      bot_response: str, session_id: Optional[int] = None) -> None:
        """Lưu 1 lượt hội thoại (user + bot)."""
        try:
            self.sql.save_conversation(user_name, user_msg, bot_response, session_id)
            print(f"[MemoryService] Saved: '{user_msg[:30]}...' -> '{bot_response[:30]}...'")
        except Exception as e:
            print(f"[MemoryService] Error saving: {e}")
    
    def get_session_history(self, session_id: int) -> list:
        """Lấy history của 1 session."""
        return self.sql.get_session_conversations(session_id)
        
    def save_context(self, session_id: str, context_dict: dict) -> None:
        """Lưu state của ConversationContext vào file JSON."""
        import json
        try:
            file_path = self._get_context_file_path()
            data = {}
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {}
            
            if "contexts" not in data:
                data["contexts"] = {}
            data["contexts"][str(session_id)] = context_dict
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MemoryService] Error saving context: {e}")
            
    def load_context(self, session_id: str) -> dict:
        """Tải state của ConversationContext từ file JSON."""
        import json
        try:
            file_path = self._get_context_file_path()
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        return data.get("contexts", {}).get(str(session_id), {})
                    except json.JSONDecodeError:
                        return {}
        except Exception as e:
            print(f"[MemoryService] Error loading context: {e}")
        return {}
        
    def trigger_summarization_if_needed(self, session_id: str, llm_service) -> None:
        """Kiểm tra và tóm tắt ngầm theo các mốc [15, 30, 50, 70, 90, 110]."""
        import threading
        
        def _summarize_task():
            import json
            import re
            try:
                sid_int = int(session_id) if str(session_id).isdigit() else 1
                raw_history = self.get_session_history(sid_int)
                total_msgs = len(raw_history) if raw_history else 0
                
                context = self.load_context(session_id)
                last_summarized_count = context.get("last_summarized_count", 0)
                
                milestones = [15, 30, 50, 70, 90, 110]
                target_milestone = 0
                for m in milestones:
                    if total_msgs >= m:
                        target_milestone = m
                
                if target_milestone <= last_summarized_count:
                    return # Đã tóm tắt đến mốc này rồi
                
                # Cần tóm tắt từ last_summarized_count đến target_milestone
                new_msgs = raw_history[last_summarized_count:target_milestone]
                text_to_summarize = ""
                for um, br, _ in new_msgs:
                    text_to_summarize += f"User: {um}\nAI: {br}\n"
                
                old_summary = context.get("long_term_summary")
                if old_summary:
                    prompt = (
                        "Bạn là chuyên gia tổng hợp. Hãy ĐỌC bản tóm tắt CŨ và các tin nhắn MỚI, sau đó GỘP chúng lại thành một khối JSON duy nhất.\n"
                        "Cấu trúc JSON bắt buộc:\n"
                        "{\n"
                        '  "user_intent": "Mục đích chính của user (cập nhật nếu có)",\n'
                        '  "key_facts": ["Sự kiện cũ 1", "Sự kiện mới 2"],\n'
                        '  "summary": "Tóm tắt ngắn gọn toàn bộ diễn biến"\n'
                        "}\n\n"
                        f"TÓM TẮT CŨ:\n{json.dumps(old_summary, ensure_ascii=False, indent=2)}\n\n"
                        f"TIN NHẮN MỚI:\n{text_to_summarize}"
                    )
                else:
                    prompt = (
                        "Bạn là chuyên gia tổng hợp. Hãy tóm tắt cuộc hội thoại sau thành một khối JSON duy nhất.\n"
                        "Cấu trúc JSON bắt buộc:\n"
                        "{\n"
                        '  "user_intent": "Mục đích chính của user",\n'
                        '  "key_facts": ["Sự kiện/Thông tin quan trọng 1", "Sự kiện 2"],\n'
                        '  "summary": "Tóm tắt ngắn gọn"\n'
                        "}\n\n"
                        f"Hội thoại:\n{text_to_summarize}"
                    )
                
                print(f"[MemoryService] Bắt đầu tóm tắt ngầm (từ tin nhắn {last_summarized_count} đến {target_milestone})...")
                result_json = llm_service.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt="LUÔN LUÔN TRẢ VỀ ĐỊNH DẠNG JSON. KHÔNG KÈM THEO TEXT GIẢI THÍCH NÀO KHÁC.",
                    max_tokens=600,
                    temperature=0.3
                )
                
                # Parse JSON
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_json, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    start = result_json.find('{')
                    end = result_json.rfind('}')
                    if start != -1 and end != -1:
                        json_str = result_json[start:end+1]
                    else:
                        json_str = "{}"
                        
                parsed = json.loads(json_str)
                if parsed:
                    context["long_term_summary"] = parsed
                    context["last_summarized_count"] = target_milestone
                    self.save_context(session_id, context)
                    print(f"[MemoryService] Đã lưu tóm tắt mốc {target_milestone} thành công.")
            except Exception as e:
                print(f"[MemoryService] Lỗi khi tóm tắt ngầm: {e}")
                
        threading.Thread(target=_summarize_task, daemon=True).start()

