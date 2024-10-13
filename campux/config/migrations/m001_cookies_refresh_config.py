from .. import migration

from ...core import app


@migration.migration_class("001_cookies_refresh_config", 1)
class Migration(migration.Migration):

    async def need_migrate(self) -> bool:
        return 'campux_qzone_cookies_refresh_strategy' not in self.ap.config.data

    async def migrate(self):
        self.ap.config.data['campux_qzone_cookies_refresh_strategy'] = 'qrcode'
        await self.ap.config.dump_config()
