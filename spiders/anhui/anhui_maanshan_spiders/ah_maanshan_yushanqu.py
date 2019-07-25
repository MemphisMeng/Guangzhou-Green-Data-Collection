# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/5/7
修改者/modifier：
修改日期/update date：

网址/url： http://ysqzwgk.mas.gov.cn/opennessContent/?branch_id=57a3df762c262ea9a00aacdd&column_code=300300
备注/note：雨山区政务公开网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'ah_maanshan_yushanqu'  
    page = 21 

    url = 'http://ysqzwgk.mas.gov.cn/opennessTarget/' \
          '?branch_id=57a3df762c262ea9a00aacdd&column_code=300300&topic_id=&page={page}'

    basic_info = {'province': 3,
                  'city': 46,
                  'source_webname': '雨山区政务公开网',
                  'sp_bm': '马鞍山市雨山区环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//div[@class="m-opltbody"]//li//p[@class="u-opl01"]/a')
        for link in links:
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_title)

    def parse_title(self, response):
        title = response.xpath('//div[@class="m-content"]/h1[@class="u-dettie"]').\
            xpath('string(.)').extract_first(default='')
        if '受理' in title and '验收' not in title:
            return self.parse_url_sl(response)
        elif '批前' in title:
            return self.parse_url_nsp(response)

    def parse_url_sl(self, response):
        trs = response.xpath('//div[@id="zoom"]//td[5]/../tr')
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
                            item['date_time'] = response.xpath('string(//div[@class="m-detinfo"]//li[4])').\
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@class="is-downlist"]//'
                                                            'a[contains(@href, "/") and not(contains(@href, "@"))]')
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
            file_texts = response.xpath('//div[@class="is-downlist"]//'
                                        'a[contains(@href, "/") and not(contains(@href, "@"))]')
            if file_texts:
                item = right_item(self.basic_info, response, gs_type='受理')
                item['date_time'] = response.xpath('string(//div[@class="m-detinfo"]//li[4])'). \
                    re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                item['project_name'] = response.xpath('//div[@class="m-content"]/h1[@class="u-dettie"]').\
                    xpath('string(.)').re_first('(.*)环境影响')
                msg, attachments = get_files(response, file_texts, 1)
                item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                             "msg": msg}}, ensure_ascii=False)
                yield item

    def parse_url_nsp(self, response):
        article = response.xpath('//div[@id="zoom"]/div[@class="text"]').xpath('string(.)')
        item = right_item(self.basic_info, response, gs_type='拟审批')
        item['date_time'] = response.xpath('string(//div[@class="m-detinfo"]//li[4])'). \
            re_first('\d{4}\D\d{1,2}\D\d{1,2}')
        if '项目名称' in article:
            item['project_name'] = article.re_first('项目名称：(.*)').strip()
        if '建设地' in article:
            item['site'] = article.re_first('建设地点：(.*)'.strip())
        if '建设单位' in article:
            item['js_dw'] = article.re_first('建设单位：(.*)').strip()
        if '编制单位' in article:
            item['hp_dw'] = article.re_first('编制单位：(.*)').strip()
        file_texts = response.xpath('//div[@class="is-downlist"]//'
                                    'a[contains(@href, "/") and not(contains(@href, "@"))]')
        num = 1 if file_texts else 0
        msg, attachments = get_files(response, file_texts, num)
        item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                     "msg": msg}}, ensure_ascii=False)
        yield item
