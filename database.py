import asyncpg
import os
from config import DATABASE_URL

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
    
    # ↓↓↓ ВОТ ЭТИ 2 СТРОКИ ДОБАВИТЬ ↓↓↓
    
    # Создаем таблицы каталога
    await create_catalog_tables()
    
    # Заполняем данные Милан
    await init_milan_data()

async def get_user_role(user_id: int) -> str:
    """Получить роль пользователя"""
    async with pool.acquire() as conn:
        # Проверяем админа
        admin = await conn.fetchval(
            'SELECT user_id FROM admins WHERE user_id = $1',
            user_id
        )
        if admin:
            return 'admin'
        
        # Проверяем работника
        worker = await conn.fetchval(
            'SELECT user_id FROM workers WHERE user_id = $1',
            user_id
        )
        if worker:
            return 'worker'
        
        return 'client'



async def create_catalog_tables():
    """Создание таблиц для каталога"""
    async with pool.acquire() as conn:
        # Таблица категорий
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Таблица товаров
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                category_id INTEGER REFERENCES categories(id),
                name TEXT NOT NULL,
                base_price INTEGER NOT NULL,
                description TEXT,
                image_url TEXT,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Таблица конфигураций Милан
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS milan_configs (
                id SERIAL PRIMARY KEY,
                doors INTEGER NOT NULL,
                door_type TEXT NOT NULL,
                price INTEGER NOT NULL
            )
        ''')
        
        # Таблица опций (ручки, антресоли, ящики)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS product_options (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                option_type TEXT NOT NULL,
                price_modifier INTEGER DEFAULT 0,
                description TEXT
            )
        ''')
        
        # Таблица корзины
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                product_id INTEGER REFERENCES products(id),
                configuration JSONB,
                quantity INTEGER DEFAULT 1,
                price INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')


async def init_milan_data():
    """Заполнение начальных данных для Милан"""
    async with pool.acquire() as conn:
        # Добавляем категорию Милан
        category_id = await conn.fetchval('''
            INSERT INTO categories (name, description)
            VALUES ('Милан', 'Шкафы-купе с различными конфигурациями')
            ON CONFLICT DO NOTHING
            RETURNING id
        ''')
        
        if not category_id:
            category_id = await conn.fetchval(
                "SELECT id FROM categories WHERE name = 'Милан'"
            )
        
        # Цены Милан (двери: Турция/Рим)
        milan_prices_tr = {
            2: 11000,
            3: 14000,
            4: 21000,
            5: 24000,
            (6, 2): 25200,  # 6 дверей, 2 трубы
            (6, 1): 27000   # 6 дверей, 1 труба
        }
        
        # Цены Милан (двери: Айша)
        milan_prices_aysha = {
            2: 13000,
            3: 17000,
            4: 24000,
            5: 29000,
            (6, 2): 30000,
            (6, 1): 32000
        }
        
        # Добавляем конфигурации Турция/Рим
        for doors, price in milan_prices_tr.items():
            if isinstance(doors, tuple):
                doors_count, tubes = doors
                await conn.execute('''
                    INSERT INTO milan_configs (doors, door_type, price)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                ''', doors_count, f'Турция/Рим ({tubes} трубы)', price)
            else:
                await conn.execute('''
                    INSERT INTO milan_configs (doors, door_type, price)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                ''', doors, 'Турция/Рим', price)
        
        # Добавляем конфигурации Айша
        for doors, price in milan_prices_aysha.items():
            if isinstance(doors, tuple):
                doors_count, tubes = doors
                await conn.execute('''
                    INSERT INTO milan_configs (doors, door_type, price)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                ''', doors_count, f'Айша ({tubes} трубы)', price)
            else:
                await conn.execute('''
                    INSERT INTO milan_configs (doors, door_type, price)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                ''', doors, 'Айша', price)
        
        # Добавляем опции (ручки)
        handles = [
            ('Ручка 30см (стандарт)', 'handle', 0, 'Стандартные ручки'),
            ('Ручка 60см', 'handle', 700, '+700₽ за ручку'),
            ('Ручка 100см', 'handle', 1000, '+1000₽ за ручку'),
        ]
        
        for name, option_type, price, desc in handles:
            await conn.execute('''
                INSERT INTO product_options (name, option_type, price_modifier, description)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
            ''', name, option_type, price, desc)
        
        # Добавляем опцию выдвижных ящиков
        await conn.execute('''
            INSERT INTO product_options (name, option_type, price_modifier, description)
            VALUES ('Выдвижные ящики', 'drawers', 2000, '+2000₽')
            ON CONFLICT DO NOTHING
        ''')

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
