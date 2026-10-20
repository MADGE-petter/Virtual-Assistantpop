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
        """Lấy history của 1 session (dạng exchange)."""
        return self.sql.get_session_conversations(session_id)

    def get_session_chat_messages(self, session_id: int) -> list:
        """Lấy tất cả các đoạn chat (tính cả người dùng và bot) của session."""
        try:
            if hasattr(self.sql, 'get_session_chat_messages'):
                return self.sql.get_session_chat_messages(session_id)
            elif hasattr(self.sql, 'db') and hasattr(self.sql.db, 'get_session_chat_messages'):
                return self.sql.db.get_session_chat_messages(session_id)
        except Exception as e:
            print(f"[MemoryService] Error getting chat messages: {e}")
        return []
        
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

    def summarize_session_if_needed(self, session_id: str, llm_service) -> Optional[dict]:
        """
        Kiểm tra và tự động tóm tắt hội thoại sau mỗi 5 đoạn chat (tính cả người và bot).
        Khi đến đoạn thứ 5, 10, 15... hệ thống sẽ thinking và tóm tắt toàn bộ nội dung
        bên trên để hiểu ngữ cảnh sâu nhất trước khi trả lời.
        """
        import json
        import re
        try:
            sid_int = int(session_id) if str(session_id).isdigit() else 1
            all_messages = self.get_session_chat_messages(sid_int)
            total_msgs = len(all_messages) if all_messages else 0

            if total_msgs < 5:
                # Chưa đủ 5 đoạn chat
                return None

            context = self.load_context(session_id)
            last_summarized_count = context.get("last_summarized_count", 0)

            # Mốc tóm tắt mỗi 5 đoạn chat: 5, 10, 15, 20...
            current_milestone = (total_msgs // 5) * 5
            if current_milestone <= last_summarized_count:
                # Đã tóm tắt ở mốc này rồi
                return context.get("long_term_summary")

            print(f"[MemoryService] [Thinking] Phát hiện mốc {current_milestone} đoạn chat (tổng {total_msgs} đoạn). Bắt đầu tóm tắt ngữ cảnh hội thoại...")

            # Lấy các tin nhắn trước tin nhắn hiện tại để tóm tắt
            history_to_summarize = all_messages[:total_msgs - 1] if total_msgs > 1 else all_messages
            text_to_summarize = ""
            for row in history_to_summarize:
                sender = row[1] if len(row) > 1 else "user"
                text = row[2] if len(row) > 2 else ""
                role = "Người dùng" if sender == "user" else "Trợ lý POP"
                text_to_summarize += f"{role}: {text}\n"

            old_summary = context.get("long_term_summary")
            if old_summary:
                prompt = (
                    "Bạn là chuyên gia phân tích ngữ cảnh hội thoại. Hãy đọc bản tóm tắt cũ và các đoạn chat mới nhất dưới đây, "
                    "sau đó tổng hợp gộp lại thành một khối JSON ngắn gọn, súc tích để làm ngữ cảnh chuẩn bị trả lời tin nhắn tiếp theo.\n"
                    "Cấu trúc JSON bắt buộc:\n"
                    "{\n"
                    '  "user_intent": "Mục đích chính / yêu cầu cốt lõi xuyên suốt của người dùng",\n'
                    '  "key_facts": ["Thông tin / sự kiện quan trọng 1", "Thông tin 2"],\n'
                    '  "summary": "Tóm tắt ngắn gọn 1-2 câu diễn biến cuộc hội thoại đến hiện tại"\n'
                    "}\n\n"
                    f"TÓM TẮT TRƯỚC ĐÓ:\n{json.dumps(old_summary, ensure_ascii=False, indent=2)}\n\n"
                    f"CÁC ĐOẠN CHAT TIẾP THEO:\n{text_to_summarize}"
                )
            else:
                prompt = (
                    "Bạn là chuyên gia phân tích ngữ cảnh hội thoại. Hãy đọc các đoạn chat dưới đây "
                    "và tổng hợp thành một khối JSON ngắn gọn, súc tích để làm ngữ cảnh chuẩn bị trả lời tin nhắn tiếp theo.\n"
                    "Cấu trúc JSON bắt buộc:\n"
                    "{\n"
                    '  "user_intent": "Mục đích chính / yêu cầu cốt lõi của người dùng",\n'
                    '  "key_facts": ["Thông tin / sự kiện quan trọng 1", "Thông tin 2"],\n'
                    '  "summary": "Tóm tắt ngắn gọn 1-2 câu diễn biến cuộc hội thoại"\n'
                    "}\n\n"
                    f"CÁC ĐOẠN CHAT:\n{text_to_summarize}"
                )

            parsed_summary = None
            if llm_service:
                try:
                    result_json = llm_service.chat(
                        messages=[{"role": "user", "content": prompt}],
                        system_prompt="LUÔN LUÔN TRẢ VỀ ĐỊNH DẠNG JSON HỢP LỆ. KHÔNG KÈM TEXT GIẢI THÍCH NÀO KHÁC.",
                        max_tokens=350,
                        temperature=0.2
                    )
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
                    parsed_summary = json.loads(json_str)
                except Exception as e:
                    print(f"[MemoryService] LLM summarization call error: {e}")

            if not parsed_summary or not isinstance(parsed_summary, dict) or not parsed_summary.get("summary"):
                # Fallback: tự trích xuất nếu LLM bận hoặc gặp lỗi định dạng
                user_points = [row[2][:60] for row in history_to_summarize if len(row) > 2 and row[1] == "user"]
                parsed_summary = {
                    "user_intent": user_points[0] if user_points else "Trò chuyện tổng quát",
                    "key_facts": user_points[-3:] if len(user_points) >= 3 else user_points,
                    "summary": f"Đã trao đổi {len(history_to_summarize)} đoạn chat về: {', '.join(user_points[-2:]) if user_points else 'yêu cầu của người dùng'}."
                }

            context["long_term_summary"] = parsed_summary
            context["last_summarized_count"] = current_milestone
            self.save_context(session_id, context)
            print(f"[MemoryService] [Thinking] Tóm tắt ngữ cảnh mốc {current_milestone} thành công: {parsed_summary.get('summary')}")
            return parsed_summary

        except Exception as e:
            print(f"[MemoryService] Lỗi khi tóm tắt ngữ cảnh: {e}")
            return None

    def trigger_summarization_if_needed(self, session_id: str, llm_service) -> None:
        """Kiểm tra và kích hoạt tóm tắt ngầm nếu chưa thực hiện."""
        import threading
        threading.Thread(
            target=self.summarize_session_if_needed,
            args=(session_id, llm_service),
            daemon=True
        ).start()

