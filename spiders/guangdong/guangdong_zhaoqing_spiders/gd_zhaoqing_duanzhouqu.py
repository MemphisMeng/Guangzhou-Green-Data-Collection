# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/4/22
修改者/modifier：
修改日期/update date：

网址/url： http://www.zqdz.gov.cn/zwgkq/zdlyxxgk_21197/hjbh_21208/jsxmhjyxpjxx_21528/index.html
备注/note：端州区人民政府网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'gd_zhaoqing_duanzhouqu'  
    page = 6 

    url = 'http://www.zqdz.gov.cn/zwgkq/zdlyxxgk_21197/hjbh_21208/jsxmhjyxpjxx_21528/index_{page}.html'  

    basic_info = {'province': 6,
                  'city': 94,
                  'source_webname': '端州区人民政府网',
                  'sp_bm': '肇庆市端州区生态环境局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        yield scrapy.Request(url='http://www.zqdz.gov.cn/zwgkq/zdlyxxgk_21197/hjbh_21208/jsxmhjyxpjxx_21528/index.html',
                             callback=self.parse_url)
        for page in range(1, self.page):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//table[@class="pubTable"]//td[@class="title"]/a')
        for link in links:
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_url_title)

    def parse_url_title(self, response):
        title = response.xpath('//div[@class="articleCon"]/h2[@class="title"]').xpath('string(.)')\
            .extract_first(default='')
        if '受理' in title or '审批前' in title:
            return self.parse_url_sl(response)
        elif '批后' in title or '批复后' in title:
            return self.parse_url_sp(response)

    def parse_url_sl(self, response):
        trs = response.xpath('//div[@id="fontzoom"]//td[6]/../../tr')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test6 = ''.join(table.xpath('string(//tr[1]/td[6])').extract_first(default='').split())
                is_test = ('项目' in test2 or '规划' in test2) and '建设单位' in test3 \
                          and '建设地点' in test4 and ('环评' in test6 or '环境影响' in test6)
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='受理')
                            item['date_time'] = response.xpath('string(//div[@class="property"])'). \
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='') \
                                .strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[6])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@class="conTxt"]//a[contains(@href, "/")'
                                                            ' and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                                         "msg": msg}},
                                                        ensure_ascii=False)
                            yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格结构问题，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')

    def parse_url_sp(self, response):
        trs = response.xpath('//div[@id="fontzoom"]//td[5]/../../tr')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test1 = ''.join(table.xpath('string(//tr[1]/td[1])').extract_first(default='').split())
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                is_test = ('项目' in test1 or '规划' in test1) and '建设单位' in test2 and '建设地' in test3 and\
                          '审批时间' in test4 and '审批文号' in test5
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='审批')
                            item['date_time'] = response.xpath('string(//div[@class="property"])'). \
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[1])').extract_first(default='') \
                                .strip()
                            item['js_dw'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['pf_time'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            item['pf_num'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@class="conTxt"]//a[contains(@href, "/")'
                                                            ' and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                        "msg": msg}}, ensure_ascii=False)
                            yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='审批', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='审批', error_info='表格结构问题，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='审批', error_info='网页格式不正确，无法提取')
