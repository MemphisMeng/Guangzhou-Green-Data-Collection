# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/5/16
修改者/modifier：
修改日期/update date：

网址/url： http://www.tljq.gov.cn/public/column/25658572?type=4&catId=25047319&action=list#atab2
备注/note：铜陵市郊区人民政府网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.items import HpspiderItem
from hpspider.utils import right_item, get_files, clean_blank
from hpspider.common_extraction import ShouliExtraction, NishenpiExtraction, ShenpiExtraction, estimate_gs_type


class HpSpider(scrapy.Spider):
    name = 'ah_tongling_jiaoqu'
    page = 11

    url = 'http://www.tljq.gov.cn/site/label/165919?IsAjax=1&dataType=html'

    basic_info = {'province': 3,
                  'city': 48,
                  'source_webname': '铜陵市郊区人民政府网',
                  'sp_bm': '铜陵市郊区环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            formdata = {
                'siteId': '3900463',
                'pageSize': '15',
                'pageIndex': str(page),
                'action': 'list',
                'isDate': 'true',
                'dateFormat': 'yyyy-MM-dd',
                'length': '37',
                'organId': '25658572',
                'type': '4',
                'catId': '25106822',
                'cId': '0',
                'result': '暂无相关消息',
                'file': '/tonglijq/publicInfoList'
            }
            yield scrapy.FormRequest(url=self.url, formdata=formdata, callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//div[@class="xxgk_nav_con"]/div[@class="xxgk_navli"]//li[@class="mc"]/a')
        for link in links:
            date_time = link.xpath('string(./../../li[@class="rq"])').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_type, meta={'date_time': date_time},
                                 dont_filter=True)

    def parse_type(self, response):
        title = response.xpath('string(//h1[@class="newstitle"])').extract_first(default='')
        date_time = response.meta['date_time']
        body = response.xpath('//div[@id="zoom"]')
        files = None
        if title and body:
            gs_type = estimate_gs_type(title, body, custom=None)
            meta = {
                'title': title,
                'body': body,
                'gs_type': gs_type,
                'date_time': date_time,
                'files': files
            }
            if gs_type == '受理':
                return scrapy.Request(url=response.url, callback=self.parse_url_sl, dont_filter=True, meta=meta)
            elif gs_type == '拟审批':
                return scrapy.Request(url=response.url, callback=self.parse_url_nsp, dont_filter=True, meta=meta)
            elif gs_type == '审批':
                return scrapy.Request(url=response.url, callback=self.parse_url_pf, dont_filter=True, meta=meta)

    def parse_url_sl(self, response):
        date_time = response.meta['date_time']
        body = response.meta['body']
        gs_type = response.meta['gs_type']
        files = response.meta['files']
        extraction_obj = ShouliExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if not data:
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

    def parse_url_nsp(self, response):
        date_time = response.meta['date_time']
        body = response.meta['body']
        gs_type = response.meta['gs_type']
        files = response.meta['files']
        extraction_obj = NishenpiExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if not data:
            yield self.extract_mission(response, '提取失败')
        else:
            for d in data:
                item = right_item(self.basic_info, response, gs_type=gs_type)
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
        body = response.meta['body']
        gs_type = response.meta['gs_type']
        files = response.meta['files']
        extraction_obj = ShenpiExtraction(body, response, files=files)
        data = extraction_obj.extract()
        if not data:
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
        files = response.meta['files']
        if files:
            item['p_attachments'] = get_files(response, response.meta['files'], 1)[1]
        item['project_name'] = response.meta['title']
        item['date_time'] = response.meta['date_time']
        return item
