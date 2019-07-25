# -*- coding: utf-8 -*-
"""
coder: 蒙安哲
date: 2019/3/28

网址:  受理  http://www.leizhou.gov.cn/Default.aspx?key=important_area_list/list&id=514822e7-0009-471a-bb74-c57c929cc559&currentId=8fd14aa5-9a6f-4d4a-93bb-40134bc14d68
备注:  雷州市人民政府网站

"""

import scrapy
import json
import re
# from datetime import date
# from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table
from scrapy.selector import Selector


class HpSpider(scrapy.Spider):
    name = 'gd_zhanjiang_leizhoushi'
    page = 6
    url = 'http://www.leizhou.gov.cn/Ashx/PostHandler.ashx?action=News-GetPublishNewsList'
    basic_info = {'province': 6,
                  'city': 93,
                  'source_webname': '雷州市人民政府网站',
                  'sp_bm': '湛江市雷州市环保局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            formdata = {
                'args': json.dumps(
                    {"PageNo": str(page), "PageSize": '15', "ClassifyID": "8fd14aa5-9a6f-4d4a-93bb-40134bc14d68"}),
            }
            yield scrapy.FormRequest(url=self.url, formdata=formdata, callback=self.parse_url)

    def parse_url(self, response):
        json_dict = json.loads(response.text)
        json_data = json_dict['data']
        for data in json_data:
            formdata = {'args': json.dumps({"NewsID": data['NewsID']}), }
            if '受理' in data['Title'] and ('环境影响' in data['Title'] or '环评' in data['Title']):
                yield scrapy.FormRequest(url='http://www.leizhou.gov.cn/Ashx/PostHandler.ashx?action='
                                             'News-GetPublishNewById&NewsID=' + data['NewsID'],formdata=formdata,
                                         callback=self.parse_url_sl)

    def parse_url_sl(self, response):
        json_dict = json.loads(response.text)
        json_data = json_dict.get('data')
        if json_data:
            web_page = json_data.get('NewsContent')
            if web_page:
                trs = Selector(text=web_page).xpath('//td[5]/..')
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
                                    item['date_time'] = ''.join(re.findall('\d{4}\D\d{1,2}\D\d{1,2}',
                                                                           json_data.get('LastUpdatedDate')))  # 发布时间
                                    item['project_name'] = data_row.xpath('string(./td[2])').extract_first(
                                        default='')  # 项目名称
                                    item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='')  # 建设单位
                                    item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='')  # 环评单位
                                    item['site'] = data_row.xpath('string(./td[4])').extract_first(default='')  # 建设地点
                                    item['source_url'] = 'http://www.leizhou.gov.cn/Info.aspx?Id=' + \
                                                         ''.join(re.findall(r"&NewsID=(.*)", response.url))
                                    file_texts = data_row.xpath('.//a[contains(@href, "/")'
                                                                ' and not(contains(@href, "@"))]')
                                    if file_texts:
                                        msg, attachments = get_files(response, file_texts, 1)
                                    else:
                                        file_texts = Selector(text=web_page).xpath('//a[contains(@href, "/")'
                                                                                   ' and not(contains(@href, "@"))]')
                                        num = len(data_rows) - 1
                                        msg, attachments = get_files(response, file_texts, num)
                                    item['remark'] = json.dumps({"remark": None, "attachments":
                                        {"data": attachments, "msg": msg}}, ensure_ascii=False)
                                    yield item
                        else:
                            item = problem_item(self.basic_info, response, gs_type='受理',
                                                error_info='表格格式变化，无法提取')
                            item['problem_url'] = 'http://www.leizhou.gov.cn/Info.aspx?Id=' + \
                                                 ''.join(re.findall(r"&NewsID=(.*)", response.url))
                            yield item
                    else:
                        item = problem_item(self.basic_info, response, gs_type='受理',
                                            error_info='表格结构问题，无法提取')
                        item['problem_url'] = 'http://www.leizhou.gov.cn/Info.aspx?Id=' + \
                                             ''.join(re.findall(r"&NewsID=(.*)", response.url))
                        yield item
                else:
                    trs = Selector(text=web_page).xpath('//div[@id="print"]//td[2]/..')
                    table = format_table(merge_table(trs))
                    if trs:
                        test2 = ''.join(table.xpath('string(//tr[1]/td[1])').extract_first(default='').split())
                        test3 = ''.join(table.xpath('string(//tr[2]/td[1])').extract_first(default='').split())
                        test4 = ''.join(table.xpath('string(//tr[3]/td[1])').extract_first(default='').split())
                        test5 = ''.join(table.xpath('string(//tr[4]/td[1])').extract_first(default='').split())
                        is_test = ('项目' in test2 or '规划' in test2) and '建设单位' in test3 \
                                  and '地点' in test4 and ('环评' in test5 or '环境影响' in test5)
                        if is_test:
                            data_rows = table.xpath('//body/table/tr')
                            item = right_item(self.basic_info, response, gs_type='受理')
                            item['date_time'] = ''.join(re.findall('\d{4}\D\d{1,2}\D\d{1,2}',
                                                                   json_data.get('LastUpdatedDate')))
                            item['project_name'] = table.xpath('string(//tr[1]/td[2])').extract_first(default='')
                            item['js_dw'] = table.xpath('string(//tr[2]/td[2])').extract_first(default='')
                            item['hp_dw'] = table.xpath('string(//tr[4]/td[2])').extract_first(default='')
                            item['site'] = table.xpath('string(//tr[3]/td[2])').extract_first(default='')
                            item['problem_url'] = 'http://www.leizhou.gov.cn/Info.aspx?Id=' + \
                                                 ''.join(re.findall(r"&NewsID=(.*)", response.url))
                            file_texts = data_rows[6].xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                            if file_texts:
                                msg, attachments = get_files(response, file_texts, 1)
                            else:
                                file_texts = Selector(text=web_page).xpath('//a[contains(href,"/")'
                                                                           ' and not (contains(@href,"@"))]')
                                num = len(data_rows) - 1
                                msg, attachments = get_files(response, file_texts, num)
                            item['remark'] = json.dumps(
                                {"remark": None, "attachments": {"data": attachments, "msg": msg}},
                                ensure_ascii=False)
                            yield item
                        else:
                            item = problem_item(self.basic_info, response, gs_type='受理',
                                                error_info='表格格式变化，无法提取')
                            item['problem_url'] = 'http://www.leizhou.gov.cn/Info.aspx?Id=' + \
                                                 ''.join(re.findall(r"&NewsID=(.*)", response.url))
                            yield item
                    else:
                        content = Selector(text=web_page).xpath('//body')\
                            .xpath('string(.)').extract_first(default='')
                        if '项目名称' in content and '建设单位' in content and '建设地点' in content\
                                and ('环境影响' in content or '环评' in content):
                            item = right_item(self.basic_info, response, gs_type='受理')
                            item['date_time'] = Selector(text=web_page).xpath('string(//div[@class="time"])').\
                                re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                            item['project_name'] = ''.join(re.findall(r"项目名称：(.*?)环境报告影响表", content))
                            item['js_dw'] = ''.join(re.findall(r"建设单位：(.*?)建设地点", content))
                            item['hp_dw'] = ''.join(re.findall(r"评价机构：(.*?)受理日期", content))
                            item['site'] = ''.join(re.findall(r"建设地点：(.*?)环境影响评价", content))
                            item['source_url'] = 'http://www.leizhou.gov.cn/Info.aspx?Id=' + \
                                                 ''.join(re.findall(r"&NewsID=(.*)", response.url))
                            file_texts = Selector(text=web_page).xpath('//div[@id="print"]//a[contains(@href, "/")'
                                                                       ' and not(contains(@href, "@"))]')
                            msg, attachments = get_files(response, file_texts, 1)
                            item['remark'] = json.dumps(
                                {"remark": None, "attachments": {"data": attachments, "msg": msg}}, ensure_ascii=False)
                        else:
                            item = problem_item(self.basic_info, response, gs_type='受理',
                                                error_info='网页格式不正确，无法提取')
                            item['problem_url'] = 'http://www.leizhou.gov.cn/Info.aspx?Id=' + \
                                                 ''.join(re.findall(r"&NewsID=(.*)", response.url))
                            yield item


