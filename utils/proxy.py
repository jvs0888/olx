import enum
import random
import typing as t
from pathlib import Path
import aiohttp

try:
    from loggers.logger import logger
    from utils.decorators import utils
    from settings.config import config
except ImportError as ie:
    exit(f'{ie} :: {Path(__file__).resolve()}')


@enum.unique
class ProxyType(enum.Enum):
    HTTP: str = 'http'
    SOCKS4: str = 'socks4'
    SOCKS5: str = 'socks5'


class Proxy:
    def __init__(self, proxy_type: ProxyType = ProxyType.HTTP, anonymous: bool = False):
        self.proxy_type: str = proxy_type.value
        self.anonymous: str = 'proxies_anonymous' if anonymous else 'proxies'
        self.proxies_list: t.Optional[list] = None

    @utils.async_exception
    async def get(self) -> str:
        if self.proxies_list:
            return 'http://' + random.choice(self.proxies_list)

    @utils.async_retry()
    async def refresh(self) -> None:
        url: str = config.PROXY['url_free'].format(anonymous=self.anonymous, proxy_type=self.proxy_type)

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as response:
                response.raise_for_status()
                text: str = await response.text()

        try:
            self.proxies_list: list = text.split('\n')
            logger.info(f'{self.proxy_type} proxies list refreshed')
        except Exception as e:
            logger.exception(e)

    @utils.async_exception
    async def check(self):
        if config.PROXY['use']:
            if config.PROXY['use_free']:
                await self.refresh()
            else:
                self.proxies_list: list = [config.PROXY['http_proxy']]
                logger.info('http proxies list refreshed')


proxy = Proxy(anonymous=True)
