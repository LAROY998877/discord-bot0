import json
import os

DB_FILE = "player_data.json"

def load_all_data():
    """تحميل كل بيانات اللاعبين من الملف"""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_all_data(data):
    """حفظ البيانات بشكل فوري ودائم"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_player(user_id):
    """جلب بيانات اللاعب أو إنشاؤه تلقائياً إذا كان جديداً مع القيم الافتراضية"""
    data = load_all_data()
    uid = str(user_id)
    
    if uid not data:
        data[uid] = {
            "coins": 0,       // العملات الأساسية
            "savings": 0,     // خزنة التوفير
            "gems": 20,       // الجواهر
            "loan": 0,        // القروض والديون
            "inventory": []   // حقيبة الأغراض أو المشتريات المستقبلية
        }
        save_all_data(data)
        
    return data[uid]

def update_player(user_id, key, value):
    """تحديث قيمة محددة للاعب (مثل إضافة عملات، خصم سعر شراء، إلخ)"""
    data = load_all_data()
    uid = str(user_id)
    
    if uid not data:
        get_player(user_id)
        data = load_all_data()
        
    data[uid][key] = value
    save_all_data(data)

def add_to_player(user_id, key, amount):
    """دالة ذكية لزيادة أو إنقاص القيم مباشرة (مثل: إضافة 100 عملة أو خصم سعر شراء)"""
    data = load_all_data()
    uid = str(user_id)
    
    if uid not data:
        get_player(user_id)
        data = load_all_data()
        
    if key not in data[uid]:
        data[uid][key] = 0
        
    data[uid][key] += amount
    save_all_data(data)
