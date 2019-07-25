# -*- coding: utf-8 -*-
"""
作者/author：蒙安哲
日期/date：2019/5/9
修改者/modifier：
修改日期/update date：

网址/url： http://zwgk.mas.gov.cn/opennessContent/?branch_id=57a3df762c262ea9a00aae58
备注/note：马鞍山信息公开网
"""

import scrapy
import json
from datetime import date
from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class HpSpider(scrapy.Spider):
    name = 'ah_maanshan_cihuqu'  
    page = 2 

    url = 'http://zwgk.mas.gov.cn/opennessTarget/?branch_id=57a3df762c262ea9a00aae58&column_code=190130&page={page}'  

    basic_info = {'province': 3,
                  'city': 46,
                  'source_webname': '马鞍山信息公开网',
                  'sp_bm': '马鞍山市慈湖高新区环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//table[@class="is-xxgkTable"]//tr/td/div[@class="is-tda"]/a')
        for link in links:
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_title)

    def parse_title(self, response):
        title = response.xpath('//h2').xpath('string(.)').extract_first(default='')
        if '受理' in title and '验收' not in title:
            return self.parse_url_sl(response)
        elif '拟审批' in title or '批前' in title:
            return self.parse_url_nsp(response)
        elif ('批复' in title or '审批' in title) and '审批前' in title:
            return self.parse_url_pf(response)

    def parse_url_sl(self, response):
        item = right_item(self.basic_info, response, gs_type='受理')
        item['date_time'] = response.xpath('string(//div[@class="main"]/table//tr[2])')\
            .re_first('\d{4}\D\d{1,2}\D\d{1,2}')
        item['project_name'] = response.xpath('//h2').xpath('string(.)').re_first('(.*项目)')
        file_texts = response.xpath('//div[@class="m-article"]//'
                                    'a[contains(@href, "/") and not(contains(@href, "@"))]')
        num = 1 if file_texts else 0
        msg, attachments = get_files(response, file_texts, num)
        item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                     "msg": msg}}, ensure_ascii=False)
        yield item

    def parse_url_nsp(self, response):
        yield right_item(self.basic_info, response, gs_type='拟审批')

    def parse_url_pf(self, response):
        yield right_item(self.basic_info, response, gs_type='批复')
