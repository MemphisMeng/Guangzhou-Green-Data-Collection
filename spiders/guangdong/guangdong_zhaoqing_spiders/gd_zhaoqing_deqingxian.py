# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/4/24
修改者/modifier：
修改日期/update date：

网址/url： http://zdly.deqing.gd.cn/index.php?m=content&c=index&a=lists&catid=76
备注/note：德庆政府门户网站
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'gd_zhaoqing_deqingxian'  
    page = 2 

    url = 'http://zdly.deqing.gd.cn/index.php?m=content&c=index&a=lists&catid=76&page={page}'  

    basic_info = {'province': 6,
                  'city': 94,
                  'source_webname': '德庆政府门户网站',
                  'sp_bm': '肇庆市德庆县人民政府网'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//ul[@class="list-unstyle"]//p[@class="text-more"]/a')
        for link in links:
            title = link.xpath('string(.)').extract_first(default='')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            if '受理' in title:
                yield scrapy.Request(url=full_url, callback=self.parse_url_sl)
            elif '审批前' in title and ('环境影响' in title or '环评' in title):
                yield scrapy.Request(url=full_url, callback=self.parse_url_nsp)
            elif '批复' in title and ('环境影响' in title or '环评' in title):
                yield scrapy.Request(url=full_url, callback=self.parse_url_pf)

    def parse_url_sl(self, response):
        trs = response.xpath('//div[@id="content"]//td[5]/../../tr')
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
                            item['date_time'] = response.xpath('string(//span[@id="inputtime"])').\
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath('//div[@id="content"]//a[contains(@href, "/")'
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
            file_texts = response.xpath('//div[@id="content"]//a[contains(@href, "/")'
                                        ' and not(contains(@href, "@"))]')
            if file_texts:
                item = right_item(self.basic_info, response, gs_type='受理')
                item['date_time'] = response.xpath('string(//span[@id="inputtime"])'). \
                    re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                item['project_name'] = file_texts.xpath('string(./@title)').re_first('(.*)\.')
                msg, attachments = get_files(response, file_texts, 1)
                item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                            "msg": msg}}, ensure_ascii=False)
                yield item

    def parse_url_nsp(self, response):
        item = right_item(self.basic_info, response, gs_type='拟审批')
        item['date_time'] = response.xpath('string(//span[@id="inputtime"])').re_first('\d{4}\D\d{1,2}\D\d{1,2}')
        item['project_name'] = response.xpath('string(//div[@id="content"])').re_first('项目名称(.*)建设地点')
        if bool(item['date_time']) is False:
            item['date_time'] = response.xpath(
                '//div[@id="content"]//a[contains(@href, "/") and not(contains(@href, "@"))]')\
                .xpath('string(./@title)').extract_first(default='')
        item['site'] = response.xpath('string(//div[@id="content"])').re_first('建设地点(.*)环境影响评价机构')
        item['hp_dw'] = response.xpath('string(//div[@id="content"])').re_first('环境影响评价机构(.*)项目概况')
        item['xm_gk'] = response.xpath('string(//div[@id="content"])').re_first('项目概况(.*)主要环境')
        item['yx_cs'] = response.xpath('string(//div[@id="content"])')\
            .re_first('主要环境影响及预防或者减轻不良环境影响的对策和措施(.*)')
        yield item

    def parse_url_pf(self, response):
        trs = response.xpath('//div[@id="content"]//td[7]/../../tr')
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
                is_test = '项目名称' in test2 and '建设单位' in test3 and '建设地' in test4 and '内容' in test5 and \
                          '审批时间' in test6 and '审批文号' in test
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    for i, data_row in enumerate(data_rows):
                        if i > 0:
                            item = right_item(self.basic_info, response, gs_type='批复')
                            item['date_time'] = response.xpath('string(//span[@id="inputtime"])') \
                                .re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='').strip()
                            item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='').strip()
                            item['site'] = data_row.xpath('string(./td[4])').extract_first(default='').strip()
                            item['xm_gk'] = data_row.xpath('string(./td[5])').extract_first(default='').strip()
                            item['pf_time'] = data_row.xpath('string(./td[6])').extract_first(default='').strip()
                            item['pf_num'] = data_row.xpath('string(./td[7])').extract_first(default='').strip()
                            file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = response.xpath(
                                    '//div[@id="content"]//a[contains(@href, "/") and not(contains(@href, "@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps(
                                {"remark": None, "attachments": {"data": attachments, "msg": msg}}, ensure_ascii=False)
                            yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='批复', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='批复', error_info='表格结构问题，无法提取')
        else:
            file_texts = response.xpath('//div[@id="content"]//a[contains(@href, "/") and not(contains(@href, "@"))]')
            if file_texts:
                item = right_item(self.basic_info, response, gs_type='批复')
                item['date_time'] = response.xpath('string(//span[@id="inputtime"])').\
                    re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                item['project_name'] = file_texts.xpath('./@title').extract_first(default='')
                msg, attachments = get_files(response, file_texts, 1)
                item['remark'] = json.dumps(
                    {"remark": None, "attachments": {"data": attachments, "msg": msg}}, ensure_ascii=False)
                yield item

