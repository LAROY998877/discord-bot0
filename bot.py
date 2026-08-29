import os
import sqlite3

# التأكد من إنشاء مجلد الـ Volume تلقائياً قبل الاتصال بقاعدة البيانات
os.makedirs("/data", exist_ok=True)

# مسار قاعدة البيانات داخل الـ Volume
DB_FILE = "/data/database.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول الأساسية
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        hero TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS economy (
        user_id TEXT PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
''')

conn.commit()
