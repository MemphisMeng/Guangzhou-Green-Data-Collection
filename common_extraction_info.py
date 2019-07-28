# This file contains all the keywords that we had already encountered or came out of mind. 
# We tried to collect all the keywords together so that we could raise our efficiency by saving the time on checking the keywords on pages.
# So the file dynamic, since we frequently came to a newly often used word.


PROJECT_NAME = ['建设项目名称', '项目名称', '事项名称', '批复名称', '文件名称']

SITE = ['建设地点', '建设地址']

JS_DW = ['建设单位', '建设单位：']

HP_DW = ['环境影响评价机构', '环评机构', '环评单位', '编制单位']

XM_GK = ['项目概况', '项目基本情况', '建设规模（内容）']

YX_CS = ['主要环境影响', '环保措施']

PF_NUM = ['审批文号', '批准文号', '文号']

PF_TIME = ['审批时间', '发文时间']

PROJECT_NAME = list(set(PROJECT_NAME))
PROJECT_NAME.sort(key=lambda x: len(x), reverse=True)

SITE = list(set(SITE))
SITE.sort(key=lambda x: len(x), reverse=True)

JS_DW = list(set(JS_DW))
JS_DW.sort(key=lambda x:len(x), reverse=True)

HP_DW = list(set(HP_DW))
HP_DW.sort(key=lambda x:len(x), reverse=True)

YX_CS = list(set(YX_CS))
YX_CS.sort(key=lambda x:len(x), reverse=True)

XM_GK = list(set(XM_GK))
XM_GK.sort(key=lambda x:len(x), reverse=True)

PF_NUM = list(set(PF_NUM))
PF_NUM.sort(key=lambda x:len(x), reverse=True)

PF_TIME = list(set(PF_TIME))
PF_TIME.sort(key=lambda x:len(x), reverse=True)
