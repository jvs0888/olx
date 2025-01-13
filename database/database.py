import json
import contextlib
import typing as t
from pathlib import Path
import asyncpg

try:
    from loggers.logger import logger
    from utils.decorators import utils
    from settings.config import config
except ImportError as ie:
    exit(f'{ie} :: {Path(__file__).resolve()}')


class Database:
    def __init__(self):
        self.dsn = config.DATABASE_URL

    @contextlib.asynccontextmanager
    async def connection(self) -> t.AsyncIterator[asyncpg.Connection]:
        conn: asyncpg.Connection = await asyncpg.connect(dsn=self.dsn)
        try:
            yield conn
        finally:
            await conn.close()

    @utils.async_exception
    async def add_user(self, user_data: list) -> None:
        query: str = """
            INSERT INTO users (product_id, user_name, user_rating, user_registered, last_online, user_located)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (product_id) DO NOTHING;
        """

        values: list = [
            (
                item['product_id'], item['user_name'], item['user_rating'],
                item['user_registered'], item['last_online'], item['user_located']
            )
            for item in user_data
        ]

        async with self.connection() as conn:
            await conn.executemany(query, values)

    @utils.async_exception
    async def add_product(self, product_data: list) -> None:
        query: str = """
            INSERT INTO product_data (product_id, url, img_url, posted_at, title, price, phone, product_types, 
                                      olx_delivery, description, views)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (product_id) DO NOTHING;
        """

        values: list = [
            (
                item['product_id'], item['url'], json.dumps(item['img_url']), item['posted_at'], item['title'],
                item['price'], json.dumps(item['phone'], ensure_ascii=False),
                json.dumps(item['product_types'], ensure_ascii=False), item['olx_delivery'], item['description'],
                item['views']
            )
            for item in product_data
        ]

        async with self.connection() as conn:
            await conn.executemany(query, values)


db: Database = Database()
