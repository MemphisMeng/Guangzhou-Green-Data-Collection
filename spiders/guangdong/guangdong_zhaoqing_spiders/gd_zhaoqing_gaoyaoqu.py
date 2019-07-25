# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/4/22
修改者/modifier：
修改日期/update date：

网址/url： http://zdlyxx.gaoyao.gov.cn/hjbh/jsxmhjyxpjxx/index.shtml
备注/note：肇庆市高要区人民政府网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'gd_zhaoqing_gaoyaoqu'  
    page = 30 

    url = 'http://zdlyxx.gaoyao.gov.cn/hjbh/jsxmhjyxpjxx/index_{page}.shtml'  

    basic_info = {'province': 6,
                  'city': 94,
                  'source_webname': '肇庆市高要区人民政府网',
                  'sp_bm': '肇庆市高要区环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        yield scrapy.Request(url='http://zdlyxx.gaoyao.gov.cn/hjbh/jsxmhjyxpjxx/index.shtml', callback=self.parse_url)
        for page in range(1, self.page):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//div[@class="list"]//li/a')
        for link in links:
            title = link.xpath('string(.)').extract_first(default='')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            if '受理' in title and ('环境影响' in title or '环评' in title) and '审批' not in title:
                yield scrapy.Request(url=full_url, callback=self.parse_url_sl)
            elif '审批前' in title and ('环境影响' in title or '环评' in title):
                yield scrapy.Request(url=full_url, callback=self.parse_url_nsp)
            elif '审批后' in title and ('环境影响' in title or '环评' in title):
                yield scrapy.Request(url=full_url, callback=self.parse_url_pf)

    def parse_url_sl(self, response):
        trs = response.xpath('//div[@class="docContent"]//td[5]/../../tr')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                is_test = ('项目' in test2 or '规划' in test2) and '建设单位' in test3 \
                          and '建设地点' in test4 and ('环评' in test5 or '环境影响' in test5)
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='受理')
                            item['date_time'] = response.xpath('string(//div[@class="writeTime"])').\
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@class="docContent"]//a[contains(@href, "/")'
                                                            ' and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                        "msg": msg}}, ensure_ascii=False)
                            yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格结构问题，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')

    def parse_url_nsp(self, response):
        trs = response.xpath('//div[@class="docContent"]//tr[9]/../tr')
        if trs:
            table = format_table(merge_table(trs))
            test1 = ''.join(table.xpath('string(//tr[1]/td[1])').extract_first(default='').split())
            test2 = ''.join(table.xpath('string(//tr[2]/td[1])').extract_first(default='').split())
            test3 = ''.join(table.xpath('string(//tr[3]/td[1])').extract_first(default='').split())
            test4 = ''.join(table.xpath('string(//tr[4]/td[1])').extract_first(default='').split())
            test6 = ''.join(table.xpath('string(//tr[6]/td[1])').extract_first(default='').split())
            test7 = ''.join(table.xpath('string(//tr[7]/td[1])').extract_first(default='').split())
            test8 = ''.join(table.xpath('string(//tr[8]/td[1])').extract_first(default='').split())
            is_test = '受理时间' in test1 and '项目名称' in test2 and '建设单位' in test3 and '建设地' in test4 and \
                      '环评单位' in test6 and '内容' in test7 and '主要环境' in test8
            if is_test:
                item = right_item(self.basic_info, response, gs_type='拟审批')
                item['date_time'] = response.xpath('string(//div[@class="writeTime"])')\
                    .re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                item['project_name'] = table.xpath('string(//tr[2]/td[2])').extract_first(default='').strip()
                item['js_dw'] = table.xpath('string(//tr[3]/td[2])').extract_first(default='').strip()
                item['site'] = table.xpath('string(//tr[4]/td[2])').extract_first(default='').strip()
                item['hp_dw'] = table.xpath('string(//tr[6]/td[2])').extract_first(default='').strip()
                item['xm_gk'] = table.xpath('string(//tr[7]/td[2])').extract_first(default='').strip()
                item['yx_cs'] = table.xpath('string(//tr[8]/td[2])').extract_first(default='').strip()
                yield item
            else:
                yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='表格格式变化，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='网页格式不正确，无法提取')

    def parse_url_pf(self, response):
        trs = response.xpath('//div[@class="docContent"]//td[8]/../../tr')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                test6 = ''.join(table.xpath('string(//tr[1]/td[6])').extract_first(default='').split())
                test8 = ''.join(table.xpath('string(//tr[1]/td[8])').extract_first(default='').split())
                is_test = '项目名称' in test2 and '建设单位' in test3 and '建设地点' in test4 and '内容' in test5 and \
                          '审批时间' in test6 and '审批文号' in test8
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='审批')
                            item['date_time'] = response.xpath('string(//div[@class="writeTime"])')\
                                .re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            item['xm_gk'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            item['pf_time'] = data_row.xpath('string(./td[6])').extract_first(default='').strip()
                            item['pf_num'] = data_row.xpath('string(./td[8])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath(
                                    '//div[@class="docContent"]//a[contains(@href, "/") and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps(
                                {"remark": None, "attachments": {"data": attachments, "msg": msg}}, ensure_ascii=False)
                            yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='审批', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='审批', error_info='表格结构问题，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='审批', error_info='网页格式不正确，无法提取')
