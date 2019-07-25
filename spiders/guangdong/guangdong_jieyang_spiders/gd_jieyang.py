"""
coder: 蒙安哲
date: 2019/3/26

网址:  受理  http://www.jieyang.gov.cn/bumen/jyhbj/hjyw_gs
备注:  揭阳市人民政府门户网站

"""

# -*- coding: utf-8 -*-
import scrapy
import json
# from datetime import date
# from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'gd_jieyang'  # 地名
    page = 112   # 由于页数随时可能出现变动，最好做全局变量以方便记忆

    url = 'http://www.jieyang.gov.cn/bumen/jyhbj/hjyw_gs?pageNum={page}&pageSize=15'  # 爬虫起始地址，翻页网站

    basic_info = {'province': 6,
                  'city': 84,
                  'source_webname': '揭阳市人民政府门户网站',
                  'sp_bm': '揭阳市环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//div[@class="list"]//li/a')
        for link in links:
            title = link.xpath('string(.)').extract_first(default='')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            if '受理' in title and ('环境影响' in title or '环评' in title):
                yield scrapy.Request(url=full_url, callback=self.parse_url_sl)

    def parse_url_sl(self, response):
        trs = response.xpath('//div[@id="zoom"]//td[7]/..')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                test6 = ''.join(table.xpath('string(//tr[1]/td[6])').extract_first(default='').split())
                is_test_1 = ('项目' in test2 or '规划' in test2) and '建设单位' in test3 \
                          and '建设地点' in test4 and ('环评' in test5 or '环境影响' in test5)
                is_test_2 = ('项目' in test3 or '规划' in test3) and '建设单位' in test5 \
                          and '建设地点' in test4 and ('环评' in test6 or '环境影响' in test6)
                data_rows = table.xpath('//body/table/tr')
                if is_test_1:
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='受理')
                            item['date_time'] = response.xpath('string(//div[@class="data"])').\
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='')  # 项目名称
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='')  # 建设单位
                            item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='')  # 环评单位
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='')  # 建设地点
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@id="zoom"]//a[contains(@href, "/")'
                                                            ' and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                        "msg": msg}}, ensure_ascii=False)
                            yield item
                elif is_test_2:
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='受理')
                            item['date_time'] = response.xpath('string(//div[@class="data"])').\
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                            item['project_name'] = data_row.xpath('string(./td[3])').extract_first(default='')  # 项目名称
                            item['js_dw'] = data_row.xpath('string(./td[5])').extract_first(default='')  # 建设单位
                            item['hp_dw'] = data_row.xpath('string(./td[6])').extract_first(default='')  # 环评单位
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='')  # 建设地点
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@id="zoom"]//a[contains(@href, "/")'
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
