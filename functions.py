# -*- coding: utf-8 -*-

from scrapy.selector import Selector
from collections import Iterable
import re
from hpspider.items import HpspiderItem
from functools import reduce


def match_file(files, i=None, data_rows=None, contents=None):
    # Many websites are likely to put many cases in one page.
    # Since we collected as many files as possible, we needed to know if our collecting work was successful.
    # So we defined three situations: 
    # 1. the number of files <or = or > the number of cases.
    bg_url = None
    remark = None
    if type(files) is str:
        files = [files]
    # collect the links and filter the repetitive ones
    if len(files) != len(set(files)):
        file_url = []
        for file in files:
            if file not in file_url:
                file_url.append(file)
    else:
        file_url = files
    if i and data_rows:
        if len(file_url) == 1:
            bg_url = file_url[0]  # 环评报告链接
        elif len(file_url) == len(data_rows) - 1:
            bg_url = file_url[i - 1]  # 环评报告链接
        elif len(file_url) == 0:
            bg_url = None
        else:
            remark = '附件数量（或顺序）有误，爬虫无法提取，请核对原网站后，再进行人工提取'
    elif i and contents:
        if len(file_url) == 1:
            bg_url = file_url[0]  
        elif len(file_url) == len(contents):
            bg_url = file_url[i - 1]
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
    return bg_url, remark # remarks contain the information of errors


def get_files(response, file_texts, num):
    '''
    :param response: response signal from internet
    :param file_texts: an iterable object, selected from tag <a>.
    :param num: pages in need
    :return: 1.msg represents the relation between the numbers of files and that of cases, 2. information of attached files
    '''

    texts = []  
    files = []  
    attachments = []  # format should be like：{'name': the text of the files, 'url': links}

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

    # duplicates the files when the content of the "name" and "url" of a same of an "attachment" is repetitive
    if attachments:
        attachments = reduce(lambda x, y: x if y in x else x + [y], [[], ] + attachments)

    if len(file_texts) == 0:
        msg = 1  # no files attached
    elif len(file_texts) < num:
        msg = 2  # files fewer than cases
    elif len(file_texts) == num:
        msg = 3  # files equal to cases
    elif len(file_texts) > num:
        msg = 4  # files more than cases

    return msg, attachments


def problem_item(basic_info, response, gs_type=None, error_info=None):
    '''
    :param gs_type: define the type of the notice
    :param error_info: define the error message
    :return:item
    '''
    item = HpspiderItem()
    # content = response.xpath('//body').extract_first()
    # item['p_type'] = gs_type
    # item['p_content'] = content
    # item['p_status'] = 0
    item['problem_url'] = response.url
    item['p_province'] = basic_info.get('province')  
    item['p_city'] = basic_info.get('city')  
    item['p_approval'] = basic_info.get('sp_bm')  
    item['source_webname'] = basic_info.get('source_webname')   
    item['error_info'] = error_info
    return item


def right_item(basic_info, response, gs_type=None):
    '''
    :param gs_type: define the type of the notice
    :return: item
    '''
    item = HpspiderItem()
    item['source_url'] = response.url 
    item['province'] = basic_info.get('province')  
    item['city'] = basic_info.get('city')  
    item['sp_bm'] = basic_info.get('sp_bm')  
    item['source_webname'] = basic_info.get('source_webname')   
    item['gs_type'] = gs_type  
    return item


def merge_table(data_rows):
    '''
    This function rebuild a <table> tag to facilitate the scraping
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
    We from time to time encountered some merged cells in some HTML texts, and this method is aimed for that.
    :param table: It should be a Selector.
    :return: A table Selector without merged cells.
    '''
    data_list = []  # This initiated list is supposed to be two-dimension, reflecting the <tr>s and <td>s
    table = table.xpath('.').extract_first(default='')
    table = table.replace('<th', '<td').replace('</th', '</td').replace('<tbody>', '').replace('</tbody>', '') \
        .replace('<thead>', '').replace('</thead>', '').replace('<tfoot>', '').replace('</tfoot>', '')
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
        # Insert the another piece of data into a blank according to the colspan/rowspan of the table
        flag = True
        while flag:
            # While iterating <td>s in the data_list, extract the colspan/rowspan attribute of each tag.
            # When colspan/rowspan >=2, clear the attribute
            # Input the identical data into the next cell except the attribute colspan/rowspan (it has to be the former value minus 1
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

        # build a table with all the data in the data_list
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

