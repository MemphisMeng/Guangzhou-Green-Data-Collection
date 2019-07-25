# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/5/16
修改者/modifier：
修改日期/update date：

网址/url： http://218.22.184.155:8231/work_List_Search.aspx?LCJD=1
备注/note：铜陵市生态环境局网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.items import HpspiderItem
from hpspider.utils import right_item, get_files, clean_blank
from hpspider.common_extraction import ShouliExtraction, NishenpiExtraction, ShenpiExtraction, estimate_gs_type


class HpSpider(scrapy.Spider):
    name = 'ah_tongling_jingkaiqu'
    sl_url = 'http://218.22.184.155:8231/work_List_Search.aspx?LCJD=1&lcjd1=1&page={page}'  # 受理链接栏目
    nsp_url = 'http://218.22.184.155:8231/work_List_Search.aspx?LCJD=1&1cjd1=2&page={page}'  # 拟审批链接栏目
    pf_url = 'http://218.22.184.155:8231/work_List_Search.aspx?LCJD=1&lcjd1=0&page={page}'  # 批复链接栏目

    sl_page = 15
    nsp_page = 12
    pf_page = 10

    basic_info = {'province': 3,
                  'city': 48,
                  'source_webname': '铜陵市生态环境局网',
                  'sp_bm': '铜陵市环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.pf_page + 1):
            yield scrapy.Request(url=self.pf_url.format(page=page), callback=self.parse_url,
                                 dont_filter=True, meta={'type': '审批'})

        for page in range(1, self.sl_page + 1):
            yield scrapy.Request(url=self.sl_url.format(page=page), callback=self.parse_url,
                                 dont_filter=True, meta={'type': '受理'})

        for page in range(1, self.nsp_page + 1):
            yield scrapy.Request(url=self.nsp_url.format(page=page), callback=self.parse_url,
                                 dont_filter=True, meta={'type': '拟审批'})

    def parse_url(self, response):
        links = response.xpath('//div[@class="sider_rc"]//li/a')
        for link in links:
            date_time = link.xpath('string(./../cite)').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            _type = response.meta['type']
            if _type == '受理':
                yield scrapy.Request(url=full_url, callback=self.parse_url_sl, meta={'date_time': date_time},
                                     dont_filter=True)
            elif _type == '拟审批':
                yield scrapy.Request(url=full_url, callback=self.parse_url_nsp, meta={'date_time': date_time},
                                     dont_filter=True)
            elif _type == '审批':
                yield scrapy.Request(url=full_url, callback=self.parse_url_pf, meta={'date_time': date_time},
                                     dont_filter=True)

    def parse_url_sl(self, response):
        date_time = response.meta['date_time']
        body = response.xpath('//div[@id="article_info"]')
        files = None
        extraction_obj = ShouliExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if not data:
            yield self.extract_mission(response, '提取失败')
        else:
            for d in data:
                item = right_item(self.basic_info, response, gs_type='受理')
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

    def parse_url_nsp(self, response):
        date_time = response.meta['date_time']
        body = response.xpath('//div[@id="article_info"]')
        files = None
        extraction_obj = NishenpiExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if not data:
            yield self.extract_mission(response, '提取失败')
        else:
            for d in data:
                item = right_item(self.basic_info, response, gs_type='拟审批')
                item['project_name'] = clean_blank(d['project_name'])
                if d['site']:
                    item['site'] = clean_blank(d['site'])
                if d['js_dw']:
                    item['js_dw'] = clean_blank(d['js_dw'])
                if d['hp_dw']:
                    item['hp_dw'] = clean_blank(d['hp_dw'])
                item['xm_gk'] = clean_blank(d['xm_gk'])
                item['yx_cs'] = clean_blank(d['yx_cs'])
                item['date_time'] = date_time
                item['remark'] = json.dumps(
                    {'remark': None, 'attachments': {'data': d['attachments'], 'msg': d['msg']}},
                    ensure_ascii=False
                )
                yield item

    def parse_url_pf(self, response):
        date_time = response.meta['date_time']
        body = response.xpath('//div[@id="article_info"]')
        files = None
        extraction_obj = ShenpiExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if not data:
            yield self.extract_mission(response, '提取失败')
        else:
            for d in data:
                item = right_item(self.basic_info, response, gs_type='审批')
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
        if response.meta['files']:
            files = response.meta['files']
        else:
            files = response.meta['body'].xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
        if files:
            item['p_attachments'] = get_files(response, files, 1)[1]
        item['project_name'] = response.meta['title']
        item['date_time'] = response.meta['date_time']
        return item

