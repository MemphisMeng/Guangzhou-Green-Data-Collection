# -*- coding: utf-8 -*-
"""
http://www.gdep.gov.cn/hpsp/
"""
from datetime import date
import scrapy
from scrapy.utils.log import configure_logging
from hpspider.utils import merge_table, format_table, get_files, problem_item, right_item
import json
from hpspider.functions import timestamp


# This time we moved forward. We categorized the errors, which helped us find the way to improve a certain program used in a site.
class HpSpider(scrapy.Spider):
    name = 'guangdong'
    url_sl = 'http://www.gdep.gov.cn/hpsp/jsxmsp/slgg/'  
    url_nsp = 'http://www.gdep.gov.cn/hpsp/jsxmsp/spqgs/'  
    url_sp = 'http://www.gdep.gov.cn/hpsp/jsxmsp/sphgg/'  
    set_time = '2019-1-23'

    # I packed up the often used information, so that we could at least save a little bit endeavor.
    basic_info = {'province': 6,
                  'city': None,
                  'source_webname': '广东省生态环境公众网',
                  'sp_bm': '广东省生态环境厅'}
                  
    file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    exceptions = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        yield scrapy.Request(self.url_sl, meta={'gs_type': 1}, callback=self.parse_url)
        yield scrapy.Request(self.url_nsp, meta={'gs_type': 2}, callback=self.parse_url)
        yield scrapy.Request(self.url_sp, meta={'gs_type': 3}, callback=self.parse_url)

    def parse_url(self, response):
        anchors = response.xpath('//a[@class="lie"]')
        gs_type = response.meta['gs_type']
        for anchor in anchors:
            url = anchor.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            if gs_type == 1:
                yield scrapy.Request(full_url, callback=self.parse_sl)
            elif gs_type == 2:
                yield scrapy.Request(full_url, callback=self.parse_nsp)
            elif gs_type == 3:
                yield scrapy.Request(full_url, callback=self.parse_sp)

    def parse_sl(self, response):
        trs = response.xpath('//td[@class="font14b"]//td[6]/..')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                is_test = '项目名称' in test2 and '建设单位' in test3 and '建设地' in test4 \
                          and ('环评' in test5 or '环境影响' in test5)
                # To make sure the keywords above exist in the web page content
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='受理')
                            item['date_time'] = response.xpath(
                                'string(//div[@id="docShare"])').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath(
                                    '//div[@id="appendix"]//a[contains(@href, "/") and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps(
                                {"remark": None, "attachments": {"data": attachments, "msg": msg}}, ensure_ascii=False)
                            if timestamp(item['date_time']) > timestamp(self.set_time):
                                yield item
                else: # changes happened to the table
                    yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')
            else:  # structural problems
                yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格结构问题，无法提取')
        else: # formatic error of the web page
            yield problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')

    def parse_nsp(self, response):
        trs = response.xpath('//td[@class="font14b"]//tr[6]/../tr')
        if trs:
            table = format_table(merge_table(trs))
            test1 = ''.join(table.xpath('string(//tr[1]/td[1])').extract_first(default='').split())
            test2 = ''.join(table.xpath('string(//tr[2]/td[1])').extract_first(default='').split())
            test3 = ''.join(table.xpath('string(//tr[3]/td[1])').extract_first(default='').split())
            test4 = ''.join(table.xpath('string(//tr[4]/td[1])').extract_first(default='').split())
            test5 = ''.join(table.xpath('string(//tr[5]/td[1])').extract_first(default='').split())
            test6 = ''.join(table.xpath('string(//tr[6]/td[1])').extract_first(default='').split())
            is_test = '项目名称' in test1 and '建设单位' in test2 and '建设地' in test3 \
                      and ('环评' in test4 or '环境影响' in test4) and '项目概况' in test5 and '主要环境' in test6
            if is_test:
                item = right_item(self.basic_info, response, gs_type='拟审批')
                item['date_time'] = response.xpath(
                    'string(//div[@id="docShare"])').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                item['project_name'] = table.xpath('string(//tr[1]/td[2])').extract_first(default='').strip()
                item['js_dw'] = table.xpath('string(//tr[2]/td[2])').extract_first(default='').strip()
                item['site'] = table.xpath('string(//tr[3]/td[2])').extract_first(default='').strip()
                item['hp_dw'] = table.xpath('string(//tr[4]/td[2])').extract_first(default='').strip()
                item['xm_gk'] = table.xpath('string(//tr[5]/td[2])').extract_first(default='').strip()
                if timestamp(item['date_time']) > timestamp(self.set_time):
                    yield item
            else:
                yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='表格格式变化，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='网页格式不正确，无法提取')

    def parse_sp(self, response):
        trs = response.xpath('//td[@class="font14b"]//td[4]/..')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                is_test = '名称' in test2 and '文号' in test3 and ('时间' in test4 or '日期' in test4)
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='审批')
                            item['date_time'] = response.xpath(
                                'string(//div[@id="docShare"])').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['pf_num'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['pf_time'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath(
                                    '//div[@id="appendix"]//a[contains(@href, "/") and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps(
                                {"remark": None, "attachments": {"data": attachments, "msg": msg}}, ensure_ascii=False)
                            if timestamp(item['date_time']) > timestamp(self.set_time):
                                yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='审批', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='审批', error_info='表格结构问题，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='审批', error_info='网页格式不正确，无法提取')
