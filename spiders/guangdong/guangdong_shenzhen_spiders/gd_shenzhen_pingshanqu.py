# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/5/27
修改者/modifier：
修改日期/update date：

网址/url： http://wsbs.sz.gov.cn/pingshan/notice
备注/note：广东政务服务网（深圳坪山区）
"""

import scrapy
import json
import re
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.items import HpspiderItem
from hpspider.utils import right_item, get_files, clean_blank
from hpspider.common_extraction import ShouliExtraction, NishenpiExtraction, ShenpiExtraction, estimate_gs_type


class HpSpider(scrapy.Spider):
    name = 'gd_shenzhen_pingshanqu'  
    page = 51

    url = 'http://wsbs.sz.gov.cn/pingshan/api-v2/action.app.notice.NoticeCmd/queryList?s=d773311559093479282'

    basic_info = {'province': 6,
                  'city': 77,
                  'source_webname': '广东政务服务网（深圳坪山区）',
                  'sp_bm': '深圳市坪山区环境保护和水务局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(self.page):
            payload = {
                'start': str(page * 10),
                'limit': str(10),
                'PUBITY_STATE': '0'
            }
            yield scrapy.Request(url=self.url.format(page=page), body=json.dumps(payload), method='POST',
                                 headers={'Content-Type': 'application/json'}, callback=self.parse_url)

    def parse_url(self, response):
        json_dict = json.loads(response.text)
        json_data = json_dict.get('data')
        for link in json_data:
            date_time = re.findall('\d{4}\D\d{1,2}\D\d{1,2}', link['START_TIME'])
            url = link['ID']
            full_url = 'http://wsbs.sz.gov.cn/pingshan/notice/details?id=' + url
            yield scrapy.Request(url=full_url, callback=self.parse_type, meta={'date_time': date_time},
                                 dont_filter=True)

    def parse_type(self, response):
        title = response.xpath('//table[@id=id="tabslist_2"]//th[text()="标题"]/../td')
        date_time = response.meta['date_time']
        body = response.xpath('//table[@id="tabslist_2"]')
        files = None
        if title and body:
            gs_type = estimate_gs_type(title, body)
            meta = {
                'title': title,
                'body': body,
                'gs_type': gs_type,
                'date_time': date_time,
                'files': files
            }
            if gs_type == '受理':
                return scrapy.Request(url=response.url, callback=self.parse_sl, dont_filter=True, meta=meta)
            elif gs_type == '拟审批':
                return scrapy.Request(url=response.url, callback=self.parse_nsp, dont_filter=True, meta=meta)
            elif gs_type == '审批':
                return scrapy.Request(url=response.url, callback=self.parse_pf, dont_filter=True, meta=meta)

    def parse_sl(self, response):
        date_time = response.meta['date_time']
        body = response.meta['body']
        gs_type = response.meta['gs_type']
        files = response.meta['files']
        extraction_obj = ShouliExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if isinstance(data, str):
            yield self.extract_mission(response, '提取失败')
        else:
            for d in data:
                item = right_item(self.basic_info, response, gs_type=gs_type)
                item['project_name'] = clean_blank(d['project_name'])
                item['site'] = clean_blank(d['site'])
                item['js_dw'] = clean_blank(d['js_dw'])
                item['hp_dw'] = clean_blank(d['hp_dw'])
                item['date_time'] = date_time
                item['remark'] = json.dumps(
                    {'remark': None, 'attachments': {'data': d['attachments'], 'msg': d['msg']}},
                    ensure_ascii=False
                )
                yield item

    def parse_nsp(self, response):
        date_time = response.meta['date_time']
        body = response.meta['body']
        gs_type = response.meta['gs_type']
        files = response.meta['files']
        extraction_obj = NishenpiExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if isinstance(data, str):
            yield self.extract_mission(response, '提取失败')
        else:
            for d in data:
                item = right_item(self.basic_info, response, gs_type=gs_type)
                item['project_name'] = clean_blank(d['project_name'])
                item['site'] = clean_blank(d['site'])
                item['js_dw'] = clean_blank(d['js_dw'])
                item['hp_dw'] = clean_blank(d['hp_dw'])
                item['js_dw'] = clean_blank(d['js_dw'])
                item['xm_gk'] = clean_blank(d['xm_gk'])
                item['yx_cs'] = clean_blank(d['yx_cs'])
                item['date_time'] = date_time
                item['remark'] = json.dumps(
                    {'remark': None, 'attachments': {'data': d['attachments'], 'msg': d['msg']}},
                    ensure_ascii=False
                )
                yield item

    def parse_pf(self, response):
        date_time = response.meta['date_time']
        body = response.meta['body']
        gs_type = response.meta['gs_type']
        files = response.meta['files']
        extraction_obj = ShenpiExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if isinstance(data, str):
            yield self.extract_mission(response, '提取失败')
        else:
            for d in data:
                item = right_item(self.basic_info, response, gs_type=gs_type)
                item['project_name'] = clean_blank(d['project_name'])
                item['date_time'] = date_time
                item['pf_num'] = clean_blank(d['pf_num'])
                item['pf_time'] = clean_blank(d['pf_time'])
                item['remark'] = json.dumps(
                    {'remark': None, 'attachments': {'data': d['attachments'], 'msg': d['msg']}},
                    ensure_ascii=False
                )
                yield item

    def extract_mission(self, response, error_info):
        """提取失败"""
        item = HpspiderItem()
        item['p_type'] = response.meta['gs_type']
        item['p_status'] = 0
        item['problem_url'] = response.url
        item['p_province'] = self.basic_info['province']
        item['p_city'] = self.basic_info['city']
        item['p_approval'] = self.basic_info['sp_bm']
        item['source_webname'] = self.basic_info['source_webname']
        item['error_info'] = error_info
        item['p_content'] = response.meta['body'].xpath('.').extract_first()
        files = response.meta['files'] if response.meta['files'] else \
            response.meta['body'].xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
        if files:
            item['p_attachments'] = get_files(response, files, 1)[1]
        item['p_project_name'] = response.meta['title']
        item['date_time'] = response.meta['date_time']
        return item
