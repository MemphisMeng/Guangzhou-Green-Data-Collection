# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/5/7
修改者/modifier：
修改日期/update date：

网址/url： http://hsqzwgk.mas.gov.cn/opennessContent/?branch_id=57a3df762c262ea9a00aacef
备注/note：花山区政府信息公开网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'ah_maanshan_huashanqu'  
    page = 12 

    url = 'http://hsqzwgk.mas.gov.cn/opennessTarget/?branch_id=57a3df762c262ea9a00aacef&column_code=350503&page={page}'  

    basic_info = {'province': 3,
                  'city': 46,
                  'source_webname': '花山区政府信息公开网',
                  'sp_bm': '马鞍山市花山区环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//table[@class="is-xxgkTable"]//tr[@class="is-td"]//div[@class="is-tda"]/a')
        for link in links:
            title = link.xpath('string(.)').extract_first(default='')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            if '受理' in title and '验收' not in title:
                yield scrapy.Request(url=full_url, callback=self.parse_url_sl)
            elif '批前' in title:
                yield scrapy.Request(url=full_url, callback=self.parse_url_nsp)
            elif ('审批' in title or '批复' in title) and '审批前' not in title:
                yield scrapy.Request(url=full_url, callback=self.parse_url_pf)

    def parse_url_sl(self, response):
        item = right_item(self.basic_info, response, gs_type='受理')
        article = response.xpath('//div[@id="zoom"]').xpath('string(.)')
        item['date_time'] = response.xpath('string(//table[@class="is-xxgkinfo"]//tr[2])').\
            re_first('\d{4}\D\d{1,2}\D\d{1,2}')
        item['project_name'] = article.re_first('项目名称：(.*)')
        item['js_dw'] = article.re_first('建设单位：(.*)')
        item['site'] = article.re_first('建设地点：(.*)')
        item['hp_dw'] = article.re_first('环境影响评价机构：（。*）')
        file_texts = response.xpath('//div[@id="color_printsssss"]//'
                                    'a[contains(@href, "/") and not(contains(@href, "@"))]')
        num = 1 if file_texts else 0
        msg, attachments = get_files(response, file_texts, num)
        item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                     "msg": msg}}, ensure_ascii=False)
        yield item

    def parse_url_nsp(self, response):
        trs = response.xpath('//div[@id="zoom"]//td[5]/../../tr')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test1 = ''.join(table.xpath('string(//tr[1]/td[1])').extract_first(default='').split())
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                test6 = ''.join(table.xpath('string(//tr[1]/td[6])').extract_first(default='').split())
                is_test_1 = ('项目' in test1 or '规划' in test1) and '建设地' in test2 and '建设单位' in test3 and\
                          ('环评' in test4 or '环境影响' in test4) and '内容' in test5 and '措施' in test6
                is_test_2 = ('项目' in test1 or '规划' in test1) and '建设地' in test2 and '建设单位' in test3 and\
                          ('环评' in test5 or '环境影响' in test5) and '内容' in test4
                if is_test_1:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='拟审批')
                            item['date_time'] = response.xpath('string(//table[@class="is-xxgkinfo"]//tr[2])'). \
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[1])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['xm_gk'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            item['yx_cs'] = data_row.xpath('string(./td[6])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@id="zoom"]//a[contains(@href, "/")'
                                                            ' and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                                         "msg": msg}},
                                                        ensure_ascii=False)
                            yield item
                elif is_test_2:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='拟审批')
                            item['date_time'] = response.xpath('string(//table[@class="is-xxgkinfo"]//tr[2])'). \
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[1])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['xm_gk'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@id="zoom"]//a[contains(@href, "/")'
                                                            ' and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                                         "msg": msg}},
                                                        ensure_ascii=False)
                            yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='表格结构问题，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='网页格式不正确，无法提取')

    def parse_url_pf(self, response):
        yield right_item(self.basic_info, response, gs_type='批复')