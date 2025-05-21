import asyncpg
import os
import datetime

DB_URL = os.getenv("DATABASE_URL")

async def get_pool():
    return await asyncpg.create_pool(dsn=DB_URL)

async def create_tables(pool):
    async with pool.acquire() as conn:
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            trial_used BOOLEAN DEFAULT FALSE,
            paid_until TIMESTAMP
        );
        ''')

async def get_user(pool, user_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)

async def set_trial_used(pool, user_id):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET trial_used=TRUE WHERE user_id=$1", user_id)

async def set_paid_until(pool, user_id, paid_until):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET paid_until=$1 WHERE user_id=$2",
            paid_until, user_id
        )

async def add_user(pool, user_id):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

async def check_access(pool, user_id):
    user = await get_user(pool, user_id)
    now = datetime.datetime.now()
    if not user:
        await add_user(pool, user_id)
        return "trial"
    if not user["trial_used"]:
        return "trial"
    if user["paid_until"] and user["paid_until"] > now:
        return "paid"
    return "no_access"
