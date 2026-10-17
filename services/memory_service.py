import sqlite3
import os

class MemoryService:
    def __init__(self, db_path="~/Workspace/AbrarAssistant/data/memory.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS conversation_history (user_id TEXT, message TEXT, response TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS file_map (user_id TEXT, filename TEXT, path TEXT)")
        self.conn.commit()

    def add_history(self, user_id, message, response):
        self.cursor.execute("INSERT INTO conversation_history VALUES (?, ?, ?)", (user_id, message, response))
        self.conn.commit()

    def get_history(self, user_id, limit=5):
        self.cursor.execute("SELECT message, response FROM conversation_history WHERE user_id=? ORDER BY rowid DESC LIMIT ?", (user_id, limit))
        return self.cursor.fetchall()
