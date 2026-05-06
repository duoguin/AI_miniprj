from google import genai
from google.genai import types
from services.tools import log_transaction, get_monthly_summary, get_category_spending
import os
api_key = os.getenv("API_KEY")  
client = genai.Client(api_key=api_key)

chat = client.chats.create(
    model='gemini-2.5-flash-lite',
    config=types.GenerateContentConfig(
        system_instruction="""Bạn là trợ lý tài chính. 
        Nhiệm vụ của bạn là ghi chép chi tiêu giúp người dùng.
        Khi người dùng khai báo chi tiêu, bạn phải tự động suy luận xem món đồ đó thuộc danh mục nào trong 5 nhóm sau: [Ăn uống, Di chuyển, Hóa đơn, Mua sắm, Lương].
        Ví dụ: Người dùng nói 'mua áo thun' -> phân loại vào 'Mua sắm'.
        Không bao giờ hỏi lại người dùng về danh mục nếu bạn có thể tự đoán được.""",
        tools=[log_transaction, get_monthly_summary, get_category_spending],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )
)

def get_chatbot_response(user_input):
    try:
        response = chat.send_message(user_input)
        if response.function_calls:
            for call in response.function_calls:
                print(f"[⚙️ HỆ THỐNG] Moni đang thực thi hàm '{call.name}' với dữ liệu: {call.args}")
        try:
            if response.text:
                print(f"Moni: {response.text}")
        except ValueError:
            # Nếu bot chỉ trả về function_call mà không kèm chữ, ta bỏ qua lỗi này
            pass
        return response.text
    except Exception as e:
        return f"Loi ket noi hoac API: {e}"

print("--- Chatbot Gemini da san sang! (Go 'exit' de thoat) ---")
while True:
    user_message = input("Ban: ")
    if user_message.lower() in ['exit', 'quit', 'thoat']:
        print("Tam biet!")
        break
        
    ai_response = get_chatbot_response(user_message)
    print(f"Gemini: {ai_response}\n")