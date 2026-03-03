import aiosqlite
from config import DATABASE_URL

DB_PATH = 'bot.db'

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'client',
                phone TEXT,
                company TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                user_id INTEGER PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

async def get_user_role(user_id: int) -> str:
    """Получить роль пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,)) as cursor:
            if await cursor.fetchone():
                return 'admin'
        
        async with db.execute('SELECT user_id FROM workers WHERE user_id = ?', (user_id,)) as cursor:
            if await cursor.fetchone():
                return 'worker'
        
        return 'client'