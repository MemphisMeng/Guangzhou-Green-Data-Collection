# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/4/22
修改者/modifier：
修改日期/update date：

网址/url： https://zdly.sg.gov.cn/website/zdly/govPublicZdly!titletype_more.action?typecode=56&css=hjbh&siteOrgCode=440233
备注/note：新丰县人民政府网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'gd_shaoguan_xinfengxian'
    page = 17

    url = 'https://zdly.sg.gov.cn/website/zdly/govPublicZdly!titletype_more.action?siteOrgCode=440233'

    basic_info = {'province': 6,
                  'city': 90,
                  'source_webname': '新丰县人民政府网',
                  'sp_bm': '韶关市新丰县环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            formdata = {
                'searchCT': '0',
                'typecode': '56',
                'css': 'hjbh',
                'currentpage': str(page),
                'pagesize': '20',
                'pageNumber': str(page)
            }
            yield scrapy.FormRequest(url=self.url, formdata=formdata, callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//div[@class="list_ul"]//li/a')
        for link in links:
            url = link.xpath('./@onclick').re_first('\'\d*\',\'(.*?)\'')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_url_sl)

    def parse_url_sl(self, response):
        title = response.xpath('//div[@class="cyy_contnet_title"]').xpath('string(.)').extract_first(default='')
        if '受理' in title and ('环境影响' in title or '环评' in title):
            trs = response.xpath('//div[@class="cyy_contnet_trct"]//td[2]/../../tr')
            if trs:
                table = format_table(merge_table(trs))
                test3 = ''.join(table.xpath('string(//tr[3]/td[1])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[4]/td[1])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[5]/td[1])').extract_first(default='').split())
                test6 = ''.join(table.xpath('string(//tr[6]/td[1])').extract_first(default='').split())
                is_test = ('项目' in test3 or '规划' in test3) and '建设地点' in test4 \
                          and '建设单位' in test5 and ('环评' in test6 or '环境影响' in test6)
                if is_test:
                    item = right_item(self.basic_info, response, gs_type='受理')
                    item['date_time'] = response.xpath('string(//table[@class="table_css"]//tr[3])').\
                        re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                    item['project_name'] = table.xpath('string(//body/table/tr[3]/td[2])').extract_first(default='')\
                        .strip()
                    item['js_dw'] = table.xpath('string(//body/table/tr[5]/td[2])').extract_first(default='').strip()
                    item['hp_dw'] = table.xpath('string(//body/table/tr[6]/td[2])').extract_first(default='').strip()
                    item['site'] = table.xpath('string(//body/table/tr[4]/td[2])').extract_first(default='').strip()
                    file_texts = table.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                    if file_texts:
                        msg, attachments = get_files(response, file_texts, 1)
                    else:
                        file_texts = response.xpath('//div[@class="cyy_contnet_trct"]//a[contains(@href, "/")'
                                                    ' and not(contains(@href, "@"))]')
                        msg, attachments = get_files(response, file_texts, 1)
                    item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                "msg": msg}}, ensure_ascii=False)
                    yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')
