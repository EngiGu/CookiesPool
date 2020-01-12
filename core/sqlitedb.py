from sqlalchemy import func


from core.model import Site, StoreCookies, session_scope
from core.status import TaskStatus
from core.utils import Utils
from core.exceptions import *


class SQLiteModel:

    def query_all_sites(self):
        with session_scope() as s:
            sites = s.query(Site).filter(Site.status == TaskStatus.ok).all()
            return sites

    # 查询site指定的cookies
    def query_site_cookies(self, site, page=1, size=20):
        page = page if page else 1
        size = size if size else 20
        with session_scope() as s:
            query = s.query(StoreCookies).join(
                Site,
                Site.id == StoreCookies.site_id
            ).filter(
                Site.site == site
            ).order_by(
                StoreCookies.id.asc()
            )

            total = s.execute(
            query.with_labels().statement.with_only_columns([func.count(1)])
        ).scalar()
            cookies = query.offset(page*(page-1)).limit(size).all()
            return total, cookies

    # 添加或者更更新一个site信息
    def add_one_site(self, site_dict):
        with session_scope() as s:
            old_record = s.query(Site).filter(Site.site == site_dict['site'])
            if not old_record.first():
                site = Site(
                    **site_dict
                )
                s.add(site)
            else:
                site_dict['modified'] = Utils.now(return_datetime=True)
                old_record.update(site_dict)

    def add_one_cookies(self, cookies_dict):
        site = cookies_dict['site']
        with session_scope() as s:
            old_record = s.query(Site).filter(
                Site.site == site
            ).first()

            if not old_record:
                raise SQLDataNULL(f'has no site record: {site}')
            cookies_dict.pop('site')
            c = StoreCookies(**cookies_dict)
            s.add(c)
            c.cookies_name = ''
            c.site_id = old_record.id
            s.flush()
            c.cookies_name = f'{site}:cookies:{c.id}'

    def update_one_cookies(self, cookies_id,  cookies: dict):
        with session_scope() as s:
            query = s.query(StoreCookies).filter(StoreCookies.id == cookies_id)
            if not query.first():
                raise SQLDataNULL('cookies do not exists!')
            cookies['modified'] = Utils.now(return_datetime=True)
            query.update(**cookies)

    def delete_one_cookies(self,  cookies_id):
        with session_scope() as s:
            s.query(StoreCookies).filter(
                StoreCookies.id == cookies_id).delete()