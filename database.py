import asyncpg
from config import DATABASE_URL, ADMIN_ID, WORKER_ID

pool = None


async def init_db():
    """Инициализация базы данных PostgreSQL"""
    global pool
    
    pool = await asyncpg.create_pool(DATABASE_URL)
    
    async with pool.acquire() as conn:
        # Таблица пользователей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'client',
                phone TEXT,
                company TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица админов
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица работников
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                user_id BIGINT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Добавляем начальных админов/работников
        await conn.execute('''
            INSERT INTO admins (user_id) VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
        ''', ADMIN_ID)
        
        await conn.execute('''
            INSERT INTO workers (user_id) VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
        ''', WORKER_ID)


async def get_user_role(user_id: int) -> str:
    """Получить роль пользователя"""
    async with pool.acquire() as conn:
        admin = await conn.fetchval(
            'SELECT user_id FROM admins WHERE user_id = $1',
            user_id
        )
        if admin:
            return 'admin'
        
        worker = await conn.fetchval(
            'SELECT user_id FROM workers WHERE user_id = $1',
            user_id
        )
        if worker:
            return 'worker'
        
        return 'client'


async def register_user(user_id: int, username: str = None, full_name: str = None):
    """Регистрация пользователя"""
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (user_id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET username = EXCLUDED.username,
                full_name = EXCLUDED.full_name
        ''', user_id, username, full_name)