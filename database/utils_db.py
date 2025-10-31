import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'storage')
DB_FILE = os.path.join(DB_DIR, 'notifier.db')

os.makedirs(DB_DIR, exist_ok=True) 

def get_db_connection():
    """获取数据库连接，启用字典访问和外键约束"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # 启用外键约束
    conn.execute("PRAGMA foreign_keys = ON")
    return conn