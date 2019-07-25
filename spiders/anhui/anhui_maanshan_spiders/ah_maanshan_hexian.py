# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/5/6
修改者/modifier：
修改日期/update date：

网址/url： http://hxzwgk.mas.gov.cn/opennessContent/?branch_id=57a3df762c262ea9a00aad5f&column_code=190100
备注/note：和县信息公开网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'ah_maanshan_hexian'  
    page = 38 

    url = 'http://hxzwgk.mas.gov.cn/opennessTarget/?branch_id=57a3df762c262ea9a00aad5f&column_code=350503&page={page}'

    basic_info = {'province': 3,
                  'city': 46,
                  'source_webname': '和县信息公开网',
                  'sp_bm': '马鞍山市和县环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//table[@class="is-xxgkTable"]//tr//div[@class="is-tda"]/a')
        for link in links:
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_url_title)

    def parse_url_title(self, response):
        title = response.xpath('//div[@class="m-article"]/h2').xpath('string(.)').extract_first(default='')
        if '受理' in title and '验收' not in title:
            return self.parse_url_sl(response)
        elif '批前' in title:
            return self.parse_url_nsp(response)
        elif '审批' in title and '审批前' not in title:
            return self.parse_url_pf(response)

    def parse_url_sl(self, response):
        file_texts = response.xpath('//div[@class="bottom"]//a[contains(@href, "/") and not(contains(@href, "@"))]')
        if file_texts:
            item = right_item(self.basic_info, response, gs_type='受理')
            item['date_time'] = response.xpath('string(//div[@class="main"]/table//tr[2])').\
                re_first('\d{4}\D\d{1,2}\D\d{1,2}')
            item['project_name'] = response.xpath('string(//div[@class="is-newstitles"])').re_first('《(.*项目)')
            msg, attachments = get_files(response, file_texts, 1)
            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments, "msg": msg}},
                                        ensure_ascii=False)
            yield item
        else:
            item = problem_item(self.basic_info, response, gs_type='受理', error_info='没有公开报告表')
            item['date_time'] = response.xpath('string(//table[@class="is-xxgkinfo"]//tr[2]/td[@class="f14"])'). \
                re_first('\d{4}\D\d{1,2}\D\d{1,2}')
            item['project_name'] = response.xpath('string(//div[@class="is-newstitles"])').re_first('《(.*项目)')
            yield item

    def parse_url_nsp(self, response):
        file_texts = response.xpath('//div[@class="bottom"]//a[contains(@href, "/") and not(contains(@href, "@"))]')
        if file_texts:
            item = right_item(self.basic_info, response, gs_type='拟审批')
            item['date_time'] = response.xpath('string(//div[@class="main"]/table//tr[2])').\
                re_first('\d{4}\D\d{1,2}\D\d{1,2}')
            item['project_name'] = response.xpath('string(//div[@class="m-article"])').re_first('项目名称：(.*)')
            item['site'] = response.xpath('string(//div[@class="m-article"])').re_first('建设地点：(.*)')
            item['js_dw'] = response.xpath('string(//div[@class="m-article"])').re_first('建设单位：(.*)')
            item['hp_dw'] = response.xpath('string(//div[@class="m-article"])').re_first('环评文件编制单位：(.*)')
            msg, attachments = get_files(response, file_texts, 1)
            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments, "msg": msg}},
                                        ensure_ascii=False)
            yield item
        else:
            yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='没有公开文件')

    def parse_url_pf(self, response):
        trs = response.xpath('//div[@class="m-article"]//td[4]/../../tr')
        if trs:
            table = format_table(merge_table(trs))
            is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
            if is_same_td:
                test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                is_test = '文件名称' in test2 and '文号' in test3 and '发文时间' in test4
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='批复')
                            item['date_time'] = response.xpath('string(//div[@class="main"]/table//tr[2])'). \
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='')
                            item['pf_num'] = data_row.xpath('string(./td[3])').extract_first(default='')
                            item['pf_time'] = data_row.xpath('string(./td[4])').extract_first(default='')
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@class="bottom"]//a[contains(@href, "/")'
                                                            ' and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                        "msg": msg}}, ensure_ascii=False)
                            yield item
