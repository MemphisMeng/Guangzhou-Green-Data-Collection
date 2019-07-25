# # -*- coding: utf-8 -*-
# """
# 作者/author：蒙安哲
# 日期/date：2019/4/10
# 修改者/modifier：
# 修改日期/update date：
# 
# 网址/url： http://www.liannan.gov.cn/Category_109/Index.aspx
# 备注/note：连南县政府网
# """
# 
# import scrapy
# import json
# from datetime import date
# from scrapy.utils.log import configure_logging
# from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table
# 
# 
# class HpSpider(scrapy.Spider):
#     name = 'gd_qingyuan_liannanxian'  
#     page = 43 
# 
#     url = 'http://www.liannan.gov.cn/Category_109/Index_{page}.aspx'  
# 
#     basic_info = {'province': 6,
#                   'city': 87,
#                   'source_webname': '连南县政府网',
#                   'sp_bm': '清远市连南县环境保护局'}
# 
#     # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
#     # exceptions = set()
# 
#     # def __init__(self, *args, **kwargs):
#     #     super().__init__(*args, **kwargs)
#     #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})
# 
#     def start_requests(self):
#         for page in range(1, self.page + 1):
#             yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)
# 
#     def parse_url(self, response):
#         links = response.xpath('//ul[@class="newsList"]/li/a')
#         for link in links:
#             title = link.xpath('./@title').extract_first(default='')
#             url = link.xpath('./@href').extract_first(default='')
#             full_url = response.urljoin(url)
#             if '受理' in title:
#                 yield scrapy.Request(url=full_url, callback=self.parse_url_sl)
# 
#     def parse_url_sl(self, response):
#         trs = response.xpath('//div[@id="fontzoom"]//td[5]/..')
#         if trs:
#             table = format_table(merge_table(trs))
#             is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
#             if is_same_td:
#                 test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
#                 test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
#                 test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
#                 test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
#                 is_test = ('项目' in test2 or '规划' in test2) and '建设单位' in test3 \
#                           and '建设地点' in test4 and ('环评' in test5 or '环境影响' in test5)
#                 if is_test:
#                     data_rows = table.xpath('//body/table/tr')
#                     for i, data_row in enumerate(data_rows):
#                         if i > 0:
#                             item = right_item(self.basic_info, response, gs_type='受理')
#                             item['date_time'] = response.xpath('string(//div[@class="property"])').\
#                                 re_first('\d{4}\D\d{1,2}\D\d{1,2}\D')  # 发布时间
#                             item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='')  # 项目名称
#                             item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='')  # 建设单位
#                             item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='')  # 环评单位
#                             item['site'] = data_row.xpath('string(./td[4])').extract_first(default='')  # 建设地点
#                             file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
#                             if file_texts:
#                                 msg, attachments = get_files(response, file_texts, 1)
#                             else:
#                                 file_texts = response.xpath('//dov[@id="fontzoom"]//a[contains(@href, "/")'
#                                                             ' and not(contains(@href, "@"))]')
#                                 num = len(data_rows) - 1
#                                 msg, attachments = get_files(response, file_texts, num)
#                             item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
#                                                         "msg": msg}}, ensure_ascii=False)
#                             yield item
#                 else:
#                     yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')
#             else:
#                 yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格结构问题，无法提取')
#         else:
#             yield problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')
# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/4/10
修改者/modifier：
修改日期/update date：

网址/url： http://www.liannan.gov.cn/Category_109/Index.aspx
备注/note：连南县政府信息公开目录系统
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.items import HpspiderItem
from hpspider.utils import right_item, get_files, clean_blank
from hpspider.common_extraction import ShouliExtraction, NishenpiExtraction, ShenpiExtraction, estimate_gs_type


class HpSpider(scrapy.Spider):
    name = 'gd_qingyuan_liannanxian'  
    page = 44

    url = 'http://www.liannan.gov.cn/Category_109/Index_44.aspx'  

    basic_info = {'province': 6,
                  'city': 87,
                  'source_webname': '连南县政府信息公开目录系统',
                  'sp_bm': '清远市连南县环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//ul[@class="newsList"]/li/a')
        for link in links:
            date_time = link.xpath('string(./../span[@class="date"])').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_type, meta={'date_time': date_time},
                                 dont_filter=True)

    def parse_type(self, response):
        title = response.xpath('string(//h2[@class="title"])').extract_first(default='')
        date_time = response.meta['date_time']
        body = response.xpath('//div[@id="fontzoom"]//table//table')
        files = None
        if title and body and '验收' not in title:
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
