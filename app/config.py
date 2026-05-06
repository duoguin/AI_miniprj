import os
import pandas as pd
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_FILE_xlsx = os.path.join(BASE_DIR, 'app/db', 'personal_transactions.xlsx')
# df = pd.read_excel(DATA_FILE_xlsx, dtype=str)
# df.to_csv("app/db/personal_transactions.csv", index=False, encoding="utf-8")

DATA_FILE = os.path.join(BASE_DIR, 'app/db', 'personal_transactions.csv')