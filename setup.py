import os

folders = [
    "app/core",
    "app/services",
    "app/models",
    "app/db",
    "app/utils",
    "data"
]

files = [
    "app/main.py",
    "app/api.py",
    "app/core/llm.py",
    "app/core/config.py",
    "app/services/expense_service.py",
    "app/db/database.py",
    "app/utils/parser.py",
    ".env",
    "requirements.txt",
    ".gitignore"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

for file in files:
    open(file, "w").close()

print("Project created.")
