from google import genai
from config import DATA_FILE
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
import os

from services.tools import (
    logTransaction,
    getMonthlySummary,
    getCategorySpending,
    getCurrentTime
)

load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)


TOOL_MAP = {
    "logTransaction": logTransaction,
    "getMonthlySummary": getMonthlySummary,
    "getCategorySpending": getCategorySpending,
    # "getCurrentTime": getCurrentTime,
}

chat = client.chats.create(
    model='gemini-2.0-flash-001',
    config=types.GenerateContentConfig(
        system_instruction="""
Bạn là trợ lý tài chính.
Current datetime: {datetime.now().isoformat()}

Danh mục:
[Ăn uống, Di chuyển, Hóa đơn, Mua sắm, Lương]
""",
        tools=[logTransaction, getMonthlySummary, getCategorySpending],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )
)


def run_chat(user_input):
    now = datetime.now().isoformat()
    full_input = f"""
        Current date: {now}
        User: {user_input}
    """
    response = chat.send_message(full_input)

    while True:
        if not response.function_calls:
            return response.text

        for call in response.function_calls:
            tool_name = call.name
            args = call.args

            print(f"[⚙️ TOOL] {tool_name} called with {args}")

            if tool_name not in TOOL_MAP:
                result = f"ERROR: Tool {tool_name} not found"
            else:
                try:
                    result = TOOL_MAP[tool_name](**args)
                except Exception as e:
                    result = f"ERROR: {e}"

            print(f"[📦 RESULT] {result}")
            print("TOOL CALL:", call.args)

            response = chat.send_message(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result}
                )
            )



print("=== Moni Chatbot Ready ===", datetime.now().isoformat())

while True:
    user_input = input("Bạn: ")

    if user_input.lower() in ["exit", "quit"]:
        break

    reply = run_chat(user_input)
    print("Moni:", reply)









#     QUY TẮC BẮT BUỘC:

# - KHÔNG BAO GIỜ hỏi người dùng về ngày giờ
# - LUÔN LUÔN sử dụng tool getCurrentTime để lấy thời gian hiện tại
# - Nếu user nói "hôm nay", "hôm qua", phải tự suy ra, KHÔNG hỏi lại

# FLOW:
# 1. Nếu thiếu date → gọi getCurrentTime
# 2. Convert sang YYYY-MM-DD
# 3. Gọi logTransaction

# VI PHẠM QUY TẮC = SAI