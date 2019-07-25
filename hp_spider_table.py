# -*- coding: utf-8 -*-
'''
You may have already noticed that there are lots of pairs of dollar signs.
Actually I coded within PyCharm, applying the living templates. (Tutorial: http://www.jetbrains.com/help/idea/using-live-templates.html)
So anyway they don't matter. They are just symbols to remind you that you put something variable into you mostly completed codes.
Just feel free to use my ideas and remember to replace the dollar signs and what are between them with what you want to code.
'''
from datetime import date
import scrapy
from scrapy.utils.log import configure_logging
from hpspider.utils import merge_table, format_table, get_files, problem_item, right_item
import json
from hpspider.functions import timestamp


class HpSpider(scrapy.Spider):
    name = '$area$'
    url = ''
    page = 8
    set_time = '1999-1-1'

    basic_info = {'province': $PROV$,
                  'city': None,
                  'source_webname': '$web$',
                  'sp_bm': '$sp_bm$'}
    
    file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    exceptions = set()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        anchors = response.xpath('//a')
        for anchor in anchors:
            title = anchor.xpath('./@title').extract_first(default='')
            url = anchor.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            if '受理' in title and ('环评' in title or '环境影响' in title):
                yield scrapy.Request(full_url, callback=self.parse_sl)
            elif '拟' in title and ('环评' in title or '环境影响' in title):
                yield scrapy.Request(full_url, callback=self.parse_nsp)
            elif '审批决定' in title and ('环评' in title or '环境影响' in title):
                yield scrapy.Request(full_url, callback=self.parse_sp)

    def parse_sl(self, response):
        trs = response.xpath('$tr$')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                is_test = '项目名称' in test2 and '建设地' in test3 and '建设单位' in test4\
                          and ('环评' in test5 or '环境影响' in test5)
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='受理')
                            item['date_time'] = response.xpath(
                                'string($time$)').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath(
                                    '$tr$//a[contains(@href, "/") and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps(
                                {"remark": None, "attachments": {"data": attachments, "msg": msg}}, ensure_ascii=False)
                            if timestamp(item['date_time']) > timestamp(self.set_time):
                                yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格结构问题，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')

    def parse_nsp(self, response):
        trs = response.xpath('$tr$')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                test6 = ''.join(table.xpath('string(//tr[1]/td[6])').extract_first(default='').split())
                test7 = ''.join(table.xpath('string(//tr[1]/td[7])').extract_first(default='').split())
                is_test = '项目名称' in test2 and '建设地' in test3 and '建设单位' in test4 \
                          and ('环评' in test5 or '环境影响' in test5) and '项目概况' in test6 and '主要环境' in test7
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='拟审批')
                            item['date_time'] = response.xpath(
                                'string($time$)').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            item['xm_gk'] = data_row.xpath('string(./td[6])').extract_first(default='').strip()
                            item['yx_cs'] = data_row.xpath('string(./td[7])').extract_first(default='').strip()
                            if timestamp(item['date_time']) > timestamp(self.set_time):
                                yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='表格结构问题，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='网页格式不正确，无法提取')

    def parse_sp(self, response):
        trs = response.xpath('$tr$')
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
                                'string($time$)').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['pf_num'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['pf_time'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath(
                                    '$tr$//a[contains(@href, "/") and not(contains(@href, "@"))]')
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
