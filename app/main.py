from services.tools import (
    logTransaction,
    getMonthlySummary,
    getCategorySpending,
    setCategoryBudget,
    getBudgetStatus,
)
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)

TOOL_MAP = {
    "logTransaction":     logTransaction,
    "getMonthlySummary":  getMonthlySummary,
    "getCategorySpending": getCategorySpending,
    "setCategoryBudget":  setCategoryBudget,
    "getBudgetStatus":    getBudgetStatus,
}

chat = client.chats.create(
    model='gemini-2.5-flash',
    config=types.GenerateContentConfig(
        system_instruction=f"""Bạn là trợ lý tài chính cá nhân. Hôm nay là {datetime.now().strftime('%Y-%m-%d')}.
Đơn vị tiền tệ: USD ($).
Danh mục: [Food & Dining, Transportation, Shopping, Bills & Utilities, Income, Entertainment, Health, Other]

Quy tắc:
- Khi người dùng báo cáo chi tiêu hoặc thu nhập, gọi logTransaction ngay lập tức mà không hỏi thêm.
- Tự động suy ra danh mục từ mô tả.
- Nếu người dùng nói "hôm nay", dùng ngày hôm nay ({datetime.now().strftime('%Y-%m-%d')}).
- KHÔNG BAO GIỜ hỏi người dùng ngày là bao nhiêu.
- Khi người dùng hỏi tình trạng ngân sách hoặc ngân sách còn lại, gọi getBudgetStatus.
- Khi người dùng muốn đặt ngân sách cho danh mục, gọi setCategoryBudget.
""",
        tools=[
            logTransaction,
            getMonthlySummary,
            getCategorySpending,
            setCategoryBudget,
            getBudgetStatus,
        ],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
)


def run_chat(user_input: str) -> str:
    now = datetime.now().isoformat()
    full_input = f"Current date: {now}\nUser: {user_input}"
    response = chat.send_message(full_input)

    # Vòng lặp xử lý thủ công các tool call từ AI
    while response.function_calls:
        # Thu thập kết quả của TẤT CẢ tool call trong cùng một lượt
        parts = []
        for call in response.function_calls:
            print(f"[⚙️ TOOL] {call.name} → {call.args}")

            if call.name not in TOOL_MAP:
                result = f"ERROR: Tool '{call.name}' không có trong TOOL_MAP"
            else:
                try:
                    result = TOOL_MAP[call.name](**call.args)
                except Exception as e:
                    result = f"ERROR: {e}"

            print(f"[📦 RESULT] {result}")
            parts.append(
                types.Part.from_function_response(
                    name=call.name,
                    response={"result": result},
                )
            )

        # Gửi toàn bộ kết quả về một lần để AI tiếp tục
        response = chat.send_message(parts)

    return response.text


if __name__ == "__main__":
    print("=== Moni Finance Chatbot Ready ===", datetime.now().isoformat())
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        reply = run_chat(user_input)
        print("Moni:", reply)
