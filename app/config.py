import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE   = os.path.join(APP_DIR, 'db', 'personal_transactions.csv')
BUDGET_FILE = os.path.join(APP_DIR, 'db', 'budgets.csv')

# Tạo file CSV với các cột chuẩn nếu file chưa tồn tại
# def init_db():
#     if not os.path.exists(DATA_FILE):
#         os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
#         with open(DATA_FILE, mode='w', encoding='utf-8') as f:
#             f.write("Date,Description,Amount,Transaction Type,Category,Account Name,Month\n")

# init_db()