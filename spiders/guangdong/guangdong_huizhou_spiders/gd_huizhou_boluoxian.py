# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/5/30
修改者/modifier：
修改日期/update date：

网址/url： http://www.boluo.gov.cn/hbj/spgggs/list.shtml
备注/note：博罗县人民政府门户网站
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.items import HpspiderItem
from hpspider.utils import right_item, get_files, clean_blank
from hpspider.common_extraction import ShouliExtraction, NishenpiExtraction, ShenpiExtraction, estimate_gs_type


class HpSpider(scrapy.Spider):
    name = 'gd_huizhou_boluoxian'

    sl_page = 188
    sl_url = 'http://www.boluo.gov.cn/hbj/slgg/list2_{page}.shtml'

    nsp_page = 19
    nsp_url = 'http://www.boluo.gov.cn/hbj/pqgs/list2_{page}.shtml'

    sp_page = 22
    sp_url = 'http://www.boluo.gov.cn/hbj/phgs/list2_{page}.shtml'

    basic_info = {'province': 6,
                  'city': 82,
                  'source_webname': '博罗县人民政府门户网站',
                  'sp_bm': '惠州市博罗县生态环境局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        yield scrapy.Request(url='http://www.boluo.gov.cn/hbj/slgg/list2.shtml',
                             meta={'gs_type': '受理'}, callback=self.parse_url)
        for page in range(2, self.sl_page + 1):
            yield scrapy.Request(url=self.sl_url.format(page=page), meta={'gs_type': '受理'}, callback=self.parse_url)

        yield scrapy.Request(url='http://www.boluo.gov.cn/hbj/pqgs/list2.shtml',
                             meta={'gs_type': '拟审批'}, callback=self.parse_url)
        for page in range(2, self.nsp_page + 1):
            yield scrapy.Request(url=self.nsp_url.format(page=page), meta={'gs_type': '拟审批'}, callback=self.parse_url)

        yield scrapy.Request(url='http://www.boluo.gov.cn/hbj/phgs/list2.shtml',
                             meta={'gs_type': '审批'}, callback=self.parse_url)
        for page in range(2, self.sp_page + 1):
            yield scrapy.Request(url=self.sp_url.format(page=page), meta={'gs_type': '审批'}, callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//div[@class="con-right fr"]//div[@class="list-right_title fon_1"]/a')
        for link in links:
            date_time = link.xpath('string(./../..//td)').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_type,
                                 meta={'date_time': date_time, 'gs_type': response.meta['gs_type']},
                                 dont_filter=True)

    def parse_type(self, response):
        title = response.xpath('string(//div[@class="con text"])').extract_first(default='')
        date_time = response.meta['date_time']
        body = response.xpath('//div[@id="zoomcon"]')
        files = None
        if title and body:
            gs_type = response.meta['gs_type']
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
