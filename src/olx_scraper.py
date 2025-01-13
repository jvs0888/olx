import json
import asyncio
import aiohttp
from pathlib import Path
from fake_useragent import UserAgent
from selectolax.lexbor import LexborHTMLParser

try:
    from loggers.logger import logger
    from utils.decorators import utils
    from settings.config import config
    from utils.proxy import proxy
    from database.database import db
except ImportError as ie:
    exit(f'{ie} :: {Path(__file__).resolve()}')


class OlxScraper:
    def __init__(self):
        self.max_page: int = 5
        self.semaphore = asyncio.Semaphore(value=self.max_page)
        self.ua: UserAgent = UserAgent(browsers='Chrome', platforms='desktop', min_version=131.0)

    @utils.async_exception
    async def get_phone(self, product_id: str) -> list:
        if product_id:
            url: str = config.URL['phone'].format(product_id=product_id)
            phone: str = await self.get_page(url=url)
            if phone:
                return json.loads(phone).get('data', {}).get('phones', None)

    @utils.exception
    def parse_product(self, product: str) -> tuple[dict, dict]:
        parser: LexborHTMLParser = LexborHTMLParser(html=product)

        # product
        element = parser.css_first('link[id="ssr_canonical"]')
        url: str = element.attributes.get('href') if element else None

        elements = parser.css('.css-1bmvjcs')
        img_url: list = [el.attributes.get('src') for el in elements] if elements else None

        element = parser.css_first('span[data-cy="ad-posted-at"]')
        posted_at: str = element.text() if element else None

        element = parser.css_first('.css-1kc83jo')
        title: str = element.text() if element else None

        element = parser.css_first('.css-90xrc0')
        price: str = element.text() if element else None

        elements = parser.css('.css-b5m1rv')
        product_types: list = [el.text() for el in elements[:-1]] if elements else None

        element = parser.css_first('div[data-testid="courier-btn"]')
        olx_delivery: bool = True if element else False

        element = parser.css_first('.css-1o924a9')
        description: str = element.text() if element else None

        element = parser.css_first('.css-12hdxwj')
        product_id: str = element.text().split()[1] if element else None

        element = parser.css_first('.css-42xwsi')
        views: str = element.text().split()[1] if element else None

        # user
        element = parser.css_first('.css-1lcz6o7')
        user_name: str = element.text() if element else None

        element = parser.css_first('.css-1b237l3')
        user_rating: str = element.text() if element else None

        element = parser.css_first('.css-23d1vy')
        user_registered: str = element.text() if element else None

        element = parser.css_first('.css-1p85e15')
        last_online: str = element.text() if element else None

        element = parser.css_first('.css-13l8eec')
        user_located: str = element.text() if element else None

        product_data: dict = {
            'url': url,
            'img_url': img_url,
            'posted_at': posted_at,
            'title': title,
            'price': price,
            'product_types': product_types,
            'olx_delivery': olx_delivery,
            'description': description,
            'product_id': product_id,
            'views': views
        }

        user_data: dict = {
            'user_name': user_name,
            'user_rating': user_rating,
            'user_registered': user_registered,
            'last_online': last_online,
            'user_located': user_located,
            'product_id': product_id
        }

        return product_data, user_data

    @utils.exception
    def parse_page(self, page: str) -> list:
        parser: LexborHTMLParser = LexborHTMLParser(html=page)

        elements: list = parser.css('a.css-qo0cxu')
        hrefs: list = [el.attributes.get('href') for el in elements]

        return list(set(hrefs))

    @utils.async_retry()
    async def get_page(self, url: str, page_num: int = None) -> str:
        config.HEADERS['user-agent'] = self.ua.random

        set_params = dict()
        if page_num:
            set_params['params'] = {'page': page_num}

        set_proxy = dict()
        if config.PROXY['use']:
            set_proxy['proxy'] = await proxy.get()

        async with self.semaphore:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(url=url,
                                       headers=config.HEADERS,
                                       **set_params,
                                       **set_proxy) as response:

                    if response.status != 400:
                        response.raise_for_status()

                    logger.info(f'{page_num if page_num else str()} page status {response.status}')
                    return await response.text()

    @utils.async_exception
    async def execute(self, tasks: list) -> list:
        # execute async tasks
        logger.info('getting pages')
        results: list = await asyncio.gather(*tasks, return_exceptions=True)

        pages = list()
        logger.info('processing pages')
        for page in results:
            if isinstance(page, Exception):
                logger.exception(page)
            else:
                pages.append(page)

        return pages

    @utils.async_exception
    async def run(self):
        # proxy check
        await proxy.check()

        # get pages with products
        tasks = list()
        for page in range(self.max_page):
            task: asyncio.Task = asyncio.create_task(self.get_page(url=config.URL['page'], page_num=page+1))
            tasks.append(task)

        pages: list = await self.execute(tasks=tasks)

        # parse pages with products
        product_urls = list()
        logger.info('parsing page')
        for page in pages:
            if page:
                product_url: list = await asyncio.to_thread(self.parse_page, page)
                product_urls.append(product_url)

        if not product_urls:
            exit('product urls not found')

        # get products separately
        tasks = list()
        for page in product_urls:
            page_products = list()
            page_users = list()

            for product_url in page:
                task: asyncio.Task = asyncio.create_task(self.get_page(url=config.URL['base']+product_url))
                tasks.append(task)

            products: list = await self.execute(tasks=tasks)

            # parse products separately
            logger.info('parsing product')
            for product in products:
                product_data, user_data = await asyncio.to_thread(self.parse_product, product)

                # get phone number
                phone: list = await self.get_phone(product_id=product_data['product_id'])
                product_data['phone'] = phone

                page_products.append(product_data)
                page_users.append(user_data)

            # save to db tables
            logger.info('saving data to db')
            await db.add_product(product_data=page_products)
            await db.add_user(user_data=page_users)
