# -*- coding: utf-8 -*-

from scrapy.selector import Selector
from collections import Iterable
import re
from hpspider.items import HpspiderItem
from functools import reduce


def match_file(files, i=None, data_rows=None, contents=None):
    bg_url = None
    remark = None
    if type(files) is str:
        files = [files]
    # 收集提取到的附件链接，判断是否有重复链接，过滤重复链接
    if len(files) != len(set(files)):
        file_url = []
        for file in files:
            if file not in file_url:
                file_url.append(file)
    else:
        file_url = files
    # 根据附件数据，以及传递的datarows、循环下标，来判断获取指定附件。
    if i and data_rows:
        if len(file_url) == 1:
            bg_url = file_url[0]  # 环评报告链接
        elif len(file_url) == len(data_rows) - 1:
            bg_url = file_url[i - 1]  # 环评报告链接
        elif len(file_url) == 0:
            bg_url = None
        else:
            remark = '附件数量（或顺序）有误，爬虫无法提取，请核对原网站后，再进行人工提取'
    # 根据附件数据，以及传递的contents、循环下标，来判断获取指定附件。
    elif i and contents:
        if len(file_url) == 1:
            bg_url = file_url[0]  # 环评报告链接
        elif len(file_url) == len(contents):
            bg_url = file_url[i - 1]  # 环评报告链接
        elif len(file_url) == 0:
            bg_url = None
        else:
            remark = '附件数量（或顺序）有误，爬虫无法提取，请核对原网站后，再进行人工提取'
    else:
        if len(file_url) == 1:
            bg_url = file_url[0]  # 环评报告链接
        elif len(file_url) == 0:
            bg_url = None
        else:
            remark = '附件数量（或顺序）有误，爬虫无法提取，请核对原网站后，再进行人工提取'
    return bg_url, remark


def get_files(response, file_texts, num):
    '''
    获取附件信息
    :param response: 抓取页面的response，用来urljoin生成完整的url
    :param file_texts: 提取到a标签的selector对象的可迭代对象,或a标签href属性的字符串，用来提取每个a标签中text和href
    :param num: 抓取页面项目数量，传参前设定
    :return: msg 1,2,3,4分别表示附件数量和项目数据的关系，attachments 储存附件信息的列表
    '''

    texts = []  # 存储附件a标签text信息
    files = []  # 存放附件链接信息
    attachments = []  # 所有附件信息 字典组成，格式：{'name': 附件文本, 'url': '附件链接'}

    if not isinstance(file_texts, list):
        file_texts = [file_texts]

    for file_text in file_texts:
        if isinstance(file_text, Selector):
            url = file_text.xpath('./@href').extract_first()
            text = file_text.xpath('string(.)').extract_first(default='')
            files.append(response.urljoin(url))
            texts.append(text)
        else:
            if isinstance(file_text, str):
                file_text = Selector(text='<a href="' + file_text + '"></a>')
                url = file_text.xpath('//a/@href').extract_first()
                text = file_text.xpath('string(.)').extract_first(default='')
                files.append(response.urljoin(url))
                texts.append(text)

    for data in zip(texts, files):
        dic = dict()
        dic['name'] = data[0]
        dic['url'] = data[1]
        attachments.append(dic)

    # 根据附件信息去重，过滤掉name和url{'name': 附件文本, 'url': '附件链接'}一样的
    if attachments:
        attachments = reduce(lambda x, y: x if y in x else x + [y], [[], ] + attachments)

    if len(file_texts) == 0:
        msg = 1  # 附件数量为零
    elif len(file_texts) < num:
        msg = 2  # 附件数量小于项目数量
    elif len(file_texts) == num:
        msg = 3  # 附件数量等于项目数量
    elif len(file_texts) > num:
        msg = 4  # 附件数量大于项目数量

    return msg, attachments


def problem_item(basic_info, response, gs_type=None, error_info=None):
    '''
    爬虫有问题的item处理
    :param gs_type: 环评公示类型
    :param error_info: 网站爬取错误提示消息
    :return:item
    '''
    item = HpspiderItem()
    # content = response.xpath('//body').extract_first()
    # item['p_type'] = gs_type
    # item['p_content'] = content
    # item['p_status'] = 0
    item['problem_url'] = response.url
    item['p_province'] = basic_info.get('province')  # 省
    item['p_city'] = basic_info.get('city')  # 市
    item['p_approval'] = basic_info.get('sp_bm')  # 审批部门
    item['source_webname'] = basic_info.get('source_webname')   # 来源网站名称
    item['error_info'] = error_info
    return item


def right_item(basic_info, response, gs_type=None):
    '''
    爬虫没问题的item处理
    :param gs_type:环评公示类型
    :return: item
    '''
    item = HpspiderItem()
    item['source_url'] = response.url  # 来源链接
    item['province'] = basic_info.get('province')  # 省
    item['city'] = basic_info.get('city')  # 市
    item['sp_bm'] = basic_info.get('sp_bm')  # 审批部门
    item['source_webname'] = basic_info.get('source_webname')   # 来源网站名称
    item['gs_type'] = gs_type  # 公示类型
    return item


def merge_table(data_rows):
    data_list = []
    for data_row in data_rows:
        data_list.append(data_row.xpath('.').extract_first(default=''))

    new_table_str = '<table>'
    for tr in data_list:
        new_table_str += tr
    new_table_str += '</table>'
    table = Selector(text=new_table_str)
    return table


def format_table(table):
    '''
    处理html文本中表格中合并单元格的问题
    :param table: 用scrapy提取html文档中的table，类型为scrapy中的Selector对象
    :return: 拆分单元格的table的Selector对象
    '''
    data_list = []  # 初始化一个空列表，二维列表，对应table中的 tr/td
    # 替换table中除了tr/td外的其他元素
    table = table.xpath('.').extract_first(default='')
    table = table.replace('<th', '<td').replace('</th', '</td').replace('<tbody>', '').replace('</tbody>', '') \
        .replace('<thead>', '').replace('</thead>', '').replace('<tfoot>', '').replace('</tfoot>', '')
    # 遍历所有table中的td, 添加到二维列表中
    trs = Selector(text=table).xpath('//body/table/tr')

    another_table = False
    for i, tr in enumerate(trs):
        tds = tr.xpath('./td')
        for j, td in enumerate(tds):
            has_rowspan = td.xpath('.//td/@rowspan')
            has_colspan = td.xpath('.//td/@rowspan')
            if has_rowspan or has_colspan:
                another_table = True

    if not another_table:
        for i, tr in enumerate(trs):
            data_list.append([])
            tds = tr.xpath('./td')
            for j, td in enumerate(tds):
                data_list[i].append(td.xpath('.').extract_first())
        # 循环根据td的colspan/rowspan属性，插入新的数据到指定一个单元格
        flag = True
        while flag:
            # 遍历 data_list 中的td，正则提取colspan/rowspan属性，大于2的话，将当前数据的colspan/rowspan属性清空
            # 并在下一个单元格插入相同数据，并用正则替换colspan/rowspan属性，将值减1
            break_flag = False
            for i, tds in enumerate(data_list):
                for j, td in enumerate(tds):
                    row = re.search('rowspan\s*?=\s*?"\s*?(\d+)\s*?"', td)
                    col = re.search('colspan\s*?=\s*?"\s*?(\d+)\s*?"', td)
                    if row and int(row.group(1)) > 1:
                        rowspan = int(row.group(1))
                        new_str_td = re.sub('rowspan\s*?=\s*?"\s*?\d+\s*?"', '', td)
                        data_list[i][j] = new_str_td
                        re_str_td = re.sub('rowspan\s*?=\s*?"\s*?(\d+)\s*?"',
                                           'rowspan="' + str(rowspan - 1) + '"', td)
                        try:
                            data_list[i + 1].insert(j, re_str_td)
                        except IndexError:
                            pass
                        break_flag = True
                        break
                    elif col and int(col.group(1)) > 1:
                        colspan = int(col.group(1))
                        new_str_td = re.sub('colspan\s*?=\s*?"\s*?\d+\s*?"', '', td)
                        data_list[i][j] = new_str_td
                        re_str_td = re.sub('colspan\s*?=\s*?"\s*?(\d+)\s*?"',
                                           'colspan="' + str(colspan - 1) + '"', td)
                        try:
                            data_list[i].insert(j + 1, re_str_td)
                        except IndexError:
                            pass
                        break_flag = True
                        break
                if break_flag:
                    break
            # 遍历 data_list 中的td，正则提取colspan/rowspan属性，判断是否大于1，大于1重新进入循环。
            flag = False
            break_flag = False
            for i, tds in enumerate(data_list):
                for j, td in enumerate(tds):
                    row = re.search('rowspan\s*?=\s*?"\s*?(\d+)\s*?"', td)
                    col = re.search('colspan\s*?=\s*?"\s*?(\d+)\s*?"', td)
                    if row and int(row.group(1)) > 1 or col and int(col.group(1)) > 1:
                        print(row, col)
                        break_flag = True
                        flag = True
                        break
                if break_flag:
                    break

        # 将data_list中的td数据进行拼接成table,并返回Seletor对象
        new_table_str = '<table>'
        for i, rows in enumerate(data_list):
            for j, data in enumerate(rows):
                if len(rows) == 1:
                    new_table_str += '<tr>' + data + '</tr>'
                if len(rows) > 1:
                    if j == 0:
                        new_table_str += '<tr>' + data
                    elif j == len(rows) - 1:
                        new_table_str += data + '</tr>'
                    else:
                        new_table_str += data
        new_table_str += '</table>'
        table = new_table_str
    else:
        pass
    table = Selector(text=table)
    return table

