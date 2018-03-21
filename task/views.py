# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import connection
from django.shortcuts import render
from task import models as taskModels
from account import models as userModels
from shared.serializers.json import Serializer, DjangoJSONEncoder
import json
from shared import Contants, Utils
from shared.serializers.serialize_json import model_to_dict
from shared.Response import Response
from shared.log import logger
from django.db.models import Q, Count, QuerySet
import os
from account.permission import login_required
from django.http import HttpResponse, FileResponse
import numpy as np
import CaliperServer.settings as settings
from django.http import StreamingHttpResponse
import uuid
from shared.Contants import TEMPFOLDER

def serialize(data, excluded='avatar'):
    return Serializer().serialize(data, excluded=excluded)


@login_required
def task(req):
    oss = taskModels.Config.objects.raw('select id,os from config GROUP by os')
    kernels = taskModels.Config.objects.raw('select id,kernel from config GROUP by kernel')
    cpus = taskModels.Cpu.objects.raw('select id,version from cpu GROUP  by version')

    # TODO 这是模拟数据
    # cpu_list=[{'id':1,'text':'Hi1612'},{'id':2,'text':'Hi1616'},{'id':3,'text':'Hi1620'},{'id':4,'text':'E5-2695'},{'id':5,'text':'E5-2697A'}]
    # os_list =[{'id':1,'text':'CentOS'},{'id':2,'text':'Ubuntu'},{'id':3,'text':'Suse'},{'id':4,'text':'Redhat'}]
    # kernel_list=[{'id':1,'text':'4.7'},{'id':2,'text':'4.8'},{'id':3,'text':'4.9'}]
    os_list = []
    cpu_list = []
    kernel_list = []
    for osObj in oss:
        os = {
            "id": osObj.os,
            "text": osObj.os
        }
        os_list.append(os)
    for kernelObj in kernels:
        kernel = {
            "id": kernelObj.kernel,
            "text": kernelObj.kernel
        }
        kernel_list.append(kernel)
    for cpuObj in cpus:
        cpu = {
            "id": cpuObj.version,
            "text": cpuObj.version
        }
        cpu_list.append(cpu)

    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').filter(delete=False)
    else:
        tasksQuery = taskModels.Task.objects.order_by('-time').filter(
            Q(owner_id=req.user.id, delete=False) | Q(shareusers__id__contains=req.user.id)).query
        tasksQuery.group_by = ['id']
        tasks = QuerySet(query=tasksQuery, model=taskModels.Task)
    obJson = req.body
    # params = json.loads(obJson)
    if obJson != '' and json.loads(obJson).has_key('page'):
        page = json.loads(obJson)['page']
    else:
        page = 1

    pageSize = Contants.PAGE_SIZE
    paginator = Paginator(tasks, pageSize)

    try:
        consumptionObjs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        consumptionObjs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        consumptionObjs = paginator.page(paginator.num_pages)

    # consumptions= Serializer().serialize(consumptionObjs,relations=('cpu',))
    consumptions = serialize(consumptionObjs)
    dict = json.loads(consumptions)
    for task in dict:
        cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
        task['config']['cpu'] = json.loads(serialize(cpus))
        sys = taskModels.System.objects.get(id=task['config']['sys'])
        task['config']['sys'] = model_to_dict(sys)

    data = {
        'cpu': json.dumps(cpu_list),
        'os': json.dumps(os_list),
        'kernel': json.dumps(kernel_list),
        'tasks': json.dumps(dict),
        'page': page,
        'pageSize': pageSize,
        'total': paginator.count,
        'isShowBack': False

    }
    print consumptionObjs.object_list
    print "============="
    return render(req, "task.html", data)


@login_required
def pageChange(req):
    try:
        obJson = req.body
        # params = json.loads(obJson)
        if obJson != '' and json.loads(obJson).has_key('page'):
            page = json.loads(obJson)['page']
        else:
            page = 1

        if req.user.role == Contants.ROLE_ADMIN:
            tasks = taskModels.Task.objects.order_by('-time').filter(delete=False)
        else:
            tasksQuery = taskModels.Task.objects.order_by('-time').filter(
                Q(owner_id=req.user.id, delete=False) | Q(shareusers__id__contains=req.user.id)).query
            tasksQuery.group_by = ['id']
            tasks = QuerySet(query=tasksQuery, model=taskModels.Task)
        pageSize = Contants.PAGE_SIZE
        paginator = Paginator(tasks, pageSize)

        try:
            consumptionObjs = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            consumptionObjs = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            consumptionObjs = paginator.page(paginator.num_pages)

        # consumptions= Serializer().serialize(consumptionObjs,relations=('cpu',))
        consumptions = serialize(consumptionObjs)
        dict = json.loads(consumptions)
        for task in dict:
            cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
            task['config']['cpu'] = json.loads(serialize(cpus))
            sys = taskModels.System.objects.get(id=task['config']['sys'])
            task['config']['sys'] = model_to_dict(sys)

        data = {
            'tasks': json.dumps(dict),
            'page': page,
            'pageSize': pageSize,
            'total': paginator.count,
        }
    except Exception as e:
        logger.error(str(e))
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")
    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)


def controlData(datas):
    ids = ""
    for index in range(len(datas)):
        data = datas[index]
        ids.join(data)
        if index + 1 < len(datas):
            ids.join(",")
    return ids


def getCpuConfigId(cpus):
    ids = []
    for cpu in cpus:
        ids.append(cpu.config_id)
    return ids


def getConfigId(configs):
    ids = []
    for config in configs:
        ids.append(config.id)
    return ids


@login_required
def filter(req):
    try:
        obJson = req.body
        page = json.loads(obJson)['page']
        filter = json.loads(obJson)['filter']
        if filter == None or len(filter) == 0 or filter == '':
            if req.user.role == Contants.ROLE_ADMIN:
                tasks = taskModels.Task.objects.order_by('-time').filter(delete=False)
            else:
                tasksQuery = taskModels.Task.objects.order_by('-time').filter(
                    Q(owner_id=req.user.id, delete=False) | Q(shareusers__id__contains=req.user.id)).query
                tasksQuery.group_by = ['id']
                tasks = QuerySet(query=tasksQuery, model=taskModels.Task)
        else:

            if not filter.has_key('kernel') and not filter.has_key('os') and not filter.has_key('cpu'):
                if req.user.role == Contants.ROLE_ADMIN:
                    tasks = taskModels.Task.objects.order_by('-time').filter(delete=False)
                else:
                    tasksQuery = taskModels.Task.objects.order_by('-time').filter(
                        Q(owner_id=req.user.id, delete=False) | Q(shareusers__id__contains=req.user.id)).query
                    tasksQuery.group_by = ['id']
                    tasks = QuerySet(query=tasksQuery, model=taskModels.Task)
            else:
                if req.user.role == Contants.ROLE_ADMIN:
                    tasksQuery = taskModels.Task.objects.order_by('-time').filter(delete=False)
                else:
                    tasksQuery = taskModels.Task.objects.order_by('-time').filter(
                        Q(owner_id=req.user.id, delete=False) | Q(shareusers__id__contains=req.user.id))

                if filter.has_key('cpu') and filter['cpu'] != '' and len(filter['cpu']) != 0:
                    cpus = filter['cpu']
                    cpuObjs = taskModels.Cpu.objects.filter(version__in=cpus)
                    tasksQuery = tasksQuery.filter(config_id__in=getCpuConfigId(cpuObjs))
                if filter.has_key('os') and filter['os'] != '' and len(filter['os']) != 0:
                    oss = filter['os']
                    configs = taskModels.Config.objects.filter(os__in=oss)
                    tasksQuery = tasksQuery.filter(config_id__in=getConfigId(configs))
                if filter.has_key('kernel') and filter['kernel'] != '' and len(filter['kernel']) != 0:
                    kernels = filter['kernel']
                    configs = taskModels.Config.objects.filter(kernel__in=kernels)
                    tasksQuery = tasksQuery.filter(config_id__in=getConfigId(configs))
                tasksQuery = tasksQuery.query
                tasksQuery.group_by = ['id']
                tasks = QuerySet(query=tasksQuery, model=taskModels.Task)

        pageSize = Contants.PAGE_SIZE
        paginator = Paginator(tasks, pageSize)
        try:
            consumptionObjs = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            consumptionObjs = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            consumptionObjs = paginator.page(paginator.num_pages)

        # consumptions= Serializer().serialize(consumptionObjs,relations=('cpu',))
        consumptions = serialize(consumptionObjs)
        dict = json.loads(consumptions)
        for task in dict:
            cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
            task['config']['cpu'] = json.loads(serialize(cpus))
            sys = taskModels.System.objects.get(id=task['config']['sys'])
            task['config']['sys'] = model_to_dict(sys)

        data = {
            'tasks': json.dumps(dict),
            'page': page,
            'pageSize': pageSize,
            'total': paginator.count,
        }
    except Exception as e:
        logger.error(str(e))
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")
    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)


def calculate(v, list):
    if list is None or len(list) == 0:
        return 0
    max = np.max(list)
    if max == 0:
        return 0
    else:
        value = v / float(max) * 100
        value = round(value, 3)
        return value

    # newList = []
    # for i in list:
    #     if max == 0:
    #         newList.append(0)
    #     else:
    #         value = i/float(max)*100
    #         value = round(value,3)
    #         newList.append(value)
    return newList


def calculate_single(value, max):
    newValue = 0
    if max == 0:
        newValue = 0
    else:
        newValue = value / float(max) * 100
        newValue = round(newValue, 3)
    return newValue


@login_required
def compare(req):
    try:
        from urllib import unquote
        # obJson = req.POST
        taskIds = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
        size = len(taskIds)
        categories = []
        dims = taskModels.Dimension.objects.all()
        for dim in dims:
            categories.append(dim.name)

        # 蛛网图 数据构造  start
        value_list = {}
        for categorie in categories:
            datas = []
            for id in taskIds:
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=id, dim__name=categorie)
                    datas.append(dimResult.result)
                except Exception as e:
                    logger.error('find dimresult none taskId:%d exception: %s',id,str(e))
                    datas.append(0)
            value_list[categorie] = datas

        series_data = []
        for index,id in enumerate(taskIds):
            data = []
            for categorie in categories:

                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=id, dim__name=categorie)
                    # data.append(dimResult.result)
                    data.append(calculate(dimResult.result, value_list[categorie]))
                except Exception as e:
                    logger.error('find dimresult none exception:%s',str(e))
                    data.append(0)
            task = taskModels.Task.objects.filter(id=id).first()
            single = {
                'name': task.name,
                'data': data,
                'visible': index == 0
                # 'pointPlacement': 'on'
            }
            series_data.append(single)
        print series_data
        # 蛛网图 数据构造  end



        # 折线图 数据构造  start
        lineSeries = []
        times = []

        for id in taskIds:
            task = taskModels.Task.objects.filter(id=id).first()
            times.append(Utils.datetime_toString(task.time))

        for index, categorie in enumerate(categories):
            data = []
            for id in taskIds:
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=id, dim__name=categorie)
                    data.append(calculate(dimResult.result, value_list[categorie]))
                except Exception as e:
                    logger.error('find dimresult none exception:%s',str(e))
                    data.append(0)

            single = {
                'name': categorie,
                'data': data,
                'visible': index == 0
                # 'pointPlacement': 'on'
            }
            lineSeries.append(single)

        print lineSeries
        # 折线图 数据构造  end

        # table 数据构造  start
        columns = []  # table column 配置
        firstCol = {
            'title': 'platform',
            'key': 'os',
            'align': 'center',
        }
        secondCOl = {
            'title': 'Date',
            'key': 'time',
            'align': 'center',
        }
        columns.append(firstCol)
        columns.append(secondCOl)
        for dim in dims:
            singleCol = {
                'title': dim.name,
                'key': dim.name,
                'align': 'center',
            }
            columns.append(singleCol)

        data_total = {}
        for cache in dims:
            vv = []
            for id in taskIds:
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=id, dim_id=cache.id)
                    vv.append(dimResult.result)
                except:
                    vv.append(0)
            data_total[cache.id] = vv

        tableData = []  # table column 对应的数据值
        for id in taskIds:
            task = taskModels.Task.objects.filter(id=id).first()
            tableSingle = {}
            tableSingle['os'] = task.config.os
            tableSingle['time'] = Utils.datetime_toString(task.time)
            for dim in dims:
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=id, dim_id=dim.id)
                    tableSingle[dim.name] = calculate_single(dimResult.result, np.max(data_total[dim.id]))
                except Exception as e:
                    logger.error('find dimresult none exception:%s',str(e))
                    tableSingle[dim.name] = 0
            tableData.append(tableSingle)
        logger.info(tableData)

        tableData = highlight(tableData, ['os', 'time'])

        # table 数据构造  end
        data = {
            'categories': json.dumps(categories),
            'series': json.dumps(series_data),
            'lineSeries': json.dumps(lineSeries),
            'times': json.dumps(times),
            'isSame': isSame(taskIds),  # 是否同一个系统平台
            'columns': json.dumps(columns),
            'tableData': json.dumps(tableData),
            'isShowBack': True
        }
        logger.info("data:%s",data)
    except Exception as e:
        logger.error(str(e))
        return render(req, "compare.html", {})
    return render(req, "compare.html", data)


def variance(values):
    '''
    计算方差
    :param values:
    :param v2:
    :return:
    '''
    if type(values) == list and 0 not in values:
        return round(np.var(values), 3)
    else:
        return 0


@login_required
def dimcompare(req, param):
    '''

    :param req:
    :param param: 维度名称
    :return:
    '''
    print param
    #  维度下的场景柱状图 数据构造  start
    categories = []
    sces = taskModels.Scenario.objects.filter(dim__name=param)
    for sce in sces:
        categories.append(sce.name)

    from urllib import unquote
    taskIds = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务

    value_list = {}
    for categorie in categories:
        datas = []
        for id in taskIds:
            try:
                dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=id)
                sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id,
                                                                  scenario__name=categorie)
                datas.append(sceResult.result)
            except:
                logger.error('find dimresult none')
                datas.append(0)
        value_list[categorie] = datas

    sce_series = []
    for index, id in enumerate(taskIds):
        sce_data = []
        for categorie in categories:
            try:
                dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=id)
                sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id,
                                                                  scenario__name=categorie)
                sce_data.append(calculate(sceResult.result, value_list[categorie]))
            except:
                sce_data.append(0)
        task = taskModels.Task.objects.filter(id=id).first()
        single = {
            'name': task.name,
            'data': sce_data,
            'visible': index == 0
            # 'pointPlacement': 'on'
        }
        sce_series.append(single)
    # 维度下的场景柱状图 数据构造  end

    # table 数据构造  start
    columns = []  # table column 配置
    firstCol = {
        'title': 'test_case',
        'key': 'name',
        'align': 'center',
    }

    columns.append(firstCol)
    for id in taskIds:
        singleCol = {
            'title': task.name,
            'key': id,
            'align': 'center',
        }
        columns.append(singleCol)
    endCol = {
        'title': 'variance',  # 方差
        'key': 'variance',
        'align': 'center',
    }
    columns.append(endCol)

    data_total = {}
    for cache in sces:
        vv = []
        for id in taskIds:
            try:
                dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=id)
                sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario_id=cache.id)
                vv.append(sceResult.result)
            except:
                vv.append(0)
        data_total[cache.id] = vv

    tableData = []  # table column 对应的数据值

    for sce in sces:
        tableSingle = {}
        tableSingle['name'] = sce.name

        values = []
        for id in taskIds:
            try:
                dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=id)
                sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario_id=sce.id)
                tableSingle[id] = calculate_single(sceResult.result, np.max(data_total[sce.id]))
                values.append(calculate_single(sceResult.result, np.max(data_total[sce.id])))
            except:
                values.append(0)
                tableSingle[id] = 0
        tableSingle['variance'] = variance(values)
        tableData.append(tableSingle)
    tableData = highlight2(tableData, taskIds[0], ['name', 'variance'])
    # table 数据构造  end

    #  维度下的场景下的testcase 折线图 数据构造  start
    #  以二维数组 表示


    case_categories = {}

    for sce in sces:
        testcases = taskModels.TestCase.objects.filter(scenario_id=sce.id)
        case_c = []
        for case in testcases:
            case_c.append(case.name)
        case_categories[sce.name] = case_c
        # case_categories.append(case_c)

    value_list = {}
    for scename, values in case_categories.items():  # 场景的集合
        case_list = {}
        for casename in values:  # case名称的集合.
            datas = []
            for index, id in enumerate(taskIds):
                try:
                    dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=id)
                    sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario__name=scename)
                    caseResult = taskModels.CaseResult.objects.get(sceResult_id=sceResult.id, case__name=casename)
                    datas.append(caseResult.result)
                except:
                    datas.append(0)
            case_list[casename] = datas
        value_list[scename] = case_list

    case_series = {}
    for scename, values in case_categories.items():  # 场景的集合
        task_case_data = []
        for index, id in enumerate(taskIds):
            case_data = []
            for casename in values:  # case名称的集合
                try:
                    dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=id)
                    sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario__name=scename)
                    caseResult = taskModels.CaseResult.objects.get(sceResult_id=sceResult.id, case__name=casename)
                    case_data.append(calculate(caseResult.result, value_list[scename][casename]))
                except:
                    case_data.append(0)
            task = taskModels.Task.objects.filter(id=id).first()
            case_signle = {
                'name': task.name,
                'data': case_data,
                'visible': index == 0
            }
            task_case_data.append(case_signle)
        case_obj = {
            'series': task_case_data,
            'categories': case_categories[scename]
        }
        case_series[scename] = case_obj

    print case_series

    #  维度下的场景下的testcase 折线图 数据构造  end


    # table 数据构造  start

    data_total = {}
    for scename, values in case_categories.items():  # 场景的集合
        caseDatas = {}
        for casename in values:  # case名称的集合
            vv = []
            for id in taskIds:
                try:
                    dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=id)
                    sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario__name=scename)
                    caseResult = taskModels.CaseResult.objects.get(sceResult_id=sceResult.id, case__name=casename)
                    vv.append(caseResult.result)
                except:
                    vv.append(0)
            caseDatas[casename] = vv
        data_total[scename] = caseDatas

    sce_table_data = {}
    for scename, values in case_categories.items():  # 场景的集合
        case_table_data = []
        caseDatas = data_total[scename]
        for casename in values:  # case名称的集合
            tableSingle = {}
            tableSingle['name'] = casename
            print casename
            print caseDatas[casename]
            values = []
            for id in taskIds:
                try:
                    dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=id)
                    sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario__name=scename)
                    caseResult = taskModels.CaseResult.objects.get(sceResult_id=sceResult.id, case__name=casename)
                    tableSingle[id] = calculate_single(caseResult.result, np.max(caseDatas[casename]))
                    values.append(calculate_single(caseResult.result, np.max(caseDatas[casename])))
                except:
                    tableSingle[id] = 0
                    values.append(0)
            tableSingle['variance'] = variance(values)
            case_table_data.append(tableSingle)
        sce_table_data[scename] = highlight2(case_table_data, taskIds[0], ['name', 'variance'])

    # table 数据构造  end




    data = {
        'categories': json.dumps(categories),
        'param': param,
        'sce_series': json.dumps(sce_series),
        'columns': json.dumps(columns),
        'tableData': json.dumps(tableData),
        # 'case_categories':json.dumps(case_categories),
        'case_series': json.dumps(case_series),
        'sce_table_data': json.dumps(sce_table_data),
        'isShowBack': True
    }
    return render(req, "dimcompare.html", data)


def highlight(tableData, exclude=[], hl=5):
    for index, td in enumerate(tableData):
        if index != 0:
            cellClassName = {}
            for key, value in td.items():
                if key in exclude:
                    continue
                firstValue = tableData[0][key]
                if value > firstValue + hl:
                    cellClassName[key] = 'table-info-row-green'
                    print '绿色'
                elif value < firstValue - hl:
                    cellClassName[key] = 'table-info-row-red'
                    print '红色'
                else:
                    print '正常'
                    cellClassName[key] = 'table-info-row-black'
            td['cellClassName'] = cellClassName
    return tableData


def highlight2(tableData, compareKey, exclude=[], hl=5):
    '''
    左右 去对比是否高亮
    :param tableData:
    :param exclude:
    :return:
    '''
    print hl
    for index, td in enumerate(tableData):
        cellClassName = {}
        for key, value in td.items():
            if key in exclude or key == compareKey:
                continue
            firstValue = td[compareKey]
            if value > firstValue + hl:
                cellClassName[key] = 'table-info-row-green'
                print '绿色'
            elif value < firstValue - hl:
                cellClassName[key] = 'table-info-row-red'
                print '红色'
            else:
                print '正常'
                cellClassName[key] = 'table-info-row-black'
        td['cellClassName'] = cellClassName
    return tableData


@login_required
def highlightChange(req):
    obJson = req.body
    if obJson is not None and obJson != "":
        obj = json.loads(obJson)
        hl = obj['highlight']
        tableData = json.loads(obj['tableData'])
        from urllib import unquote
        taskIds = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
        tableData = highlight2(tableData, str(taskIds[0]), ['name', 'variance', 'cellClassName'], hl)
        data = {
            "tableData": tableData
        }
        return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)
    else:
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")


def isSame(taskIds):
    n = len(taskIds)
    isSame = True

    for i in range(0, n):
        for j in range(i + 1, n):
            task_i = taskModels.Task.objects.filter(id=taskIds[i]).first()
            task_j = taskModels.Task.objects.filter(id=taskIds[j]).first()
            if task_j.config.os != task_i.config.os:
                isSame = False
                break

    return isSame

@login_required
def boardInfo(req):
    oss = taskModels.Config.objects.raw('select id,os from config GROUP by os')
    kernels = taskModels.Config.objects.raw('select id,kernel from config GROUP by kernel')
    cpus = taskModels.Cpu.objects.raw('select id,version from cpu GROUP  by version')

    # cpu_list=[{'id':1,'text':'Hi1612'},{'id':2,'text':'Hi1616'},{'id':3,'text':'Hi1620'},{'id':4,'text':'E5-2695'},{'id':5,'text':'E5-2697A'}]
    # os_list =[{'id':1,'text':'CentOS'},{'id':2,'text':'Ubuntu'},{'id':3,'text':'Suse'},{'id':4,'text':'Redhat'}]
    # kernel_list=[{'id':1,'text':'4.7'},{'id':2,'text':'4.8'},{'id':3,'text':'4.9'}]
    os_list = []
    cpu_list = []
    kernel_list = []
    for osObj in oss:
        os = {
            "id": osObj.os,
            "text": osObj.os
        }
        os_list.append(os)
    for kernelObj in kernels:
        kernel = {
            "id": kernelObj.kernel,
            "text": kernelObj.kernel
        }
        kernel_list.append(kernel)
    for cpuObj in cpus:
        cpu = {
            "id": cpuObj.version,
            "text": cpuObj.version
        }
        cpu_list.append(cpu)

    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        # tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)
        # return HttpResponse(status=403, content='不是管理员权限,访问受限')
        return HttpResponse(status=403, content='Not administrator privileges, limited access')

    obJson = req.body
    # params = json.loads(obJson)
    if obJson != '' and json.loads(obJson).has_key('page'):
        page = json.loads(obJson)['page']
    else:
        page = 1

    pageSize = Contants.PAGE_SIZE
    paginator = Paginator(tasks, pageSize)

    try:
        consumptionObjs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        consumptionObjs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        consumptionObjs = paginator.page(paginator.num_pages)

    # consumptions= Serializer().serialize(consumptionObjs,relations=('cpu',))
    consumptions = serialize(consumptionObjs)
    dict = json.loads(consumptions)
    for task in dict:
        cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
        task['config']['cpu'] = json.loads(serialize(cpus))
        sys = taskModels.System.objects.get(id=task['config']['sys'])
        task['config']['sys'] = model_to_dict(sys)

    data = {
        'cpu': json.dumps(cpu_list),
        'os': json.dumps(os_list),
        'kernel': json.dumps(kernel_list),
        'tasks': json.dumps(dict),
        'page': page,
        'pageSize': pageSize,
        'total': paginator.count,
        'isShowBack': True
    }
    print data['total']
    # print consumptionObjs.object_list
    return render(req, "boardInfo.html", data)


@login_required
def stateSearchUser(req):
    if not req.POST:
        return HttpResponse(status=403)
    data = req.POST
    searchUserName = data.get('searchUserName')
    searchState = data.get('searchState')
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        return HttpResponse(status=403, content='Not administrator privileges, limited access')
    if searchUserName:
        tasks = tasks.filter(owner__username=searchUserName)
    if searchState == "delRow":
        tasks = tasks.filter(delete=1)
    elif searchState == "normal":
        tasks = tasks.filter(delete=0)
    else:
        pass

    try:
        if not tasks:
            print tasks
            return HttpResponse(status=404)
        pageSize = Contants.PAGE_SIZE
        paginator = Paginator(tasks, pageSize)
        try:
            consumptionObjs = paginator.page(1)
        except EmptyPage:
            consumptionObjs = paginator.page(paginator.num_pages)
        consumptions = serialize(consumptionObjs)
        dict = json.loads(consumptions)
        for task in dict:
            cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
            task['config']['cpu'] = json.loads(serialize(cpus))
            sys = taskModels.System.objects.get(id=task['config']['sys'])
            task['config']['sys'] = model_to_dict(sys)

            data = {
                'tasks': json.dumps(dict),
                'page': 1,
                'pageSize': pageSize,
                'total': paginator.count,
            }

    except Exception as e:
        logger.error(str(e))
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")
    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)


@login_required
def statePageChange(req):
    try:
        obJson = req.body
        data = json.loads(obJson)
        # params = json.loads(obJson)
        page = data.get('page')
        searchUserName = data.get('searchUserName')
        searchState = data.get('searchUserName')
        if not page: page = 1
        if req.user.role == Contants.ROLE_ADMIN:
            tasks = taskModels.Task.objects.order_by('-time').all()
            if searchUserName != '' and not searchUserName:
                tasks = tasks.filter(owner__username="{}".format(searchUserName))
            if searchState == 'normal':
                tasks = tasks.filter(delete=0)
            elif searchState == 'delRow':
                tasks = tasks.filter(delete=1)
            else:
                pass
        else:
            # tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)
            # if searchUserName != '' and not searchUserName:
            #     tasks = tasks.filter(owner__username="{}".format(searchUserName))
            # if searchState == 'normal':
            #     tasks = tasks.filter(delete=0)
            # elif searchState == 'delRow':
            #     tasks = tasks.filter(delete=1)
            # else:
            #     pass
            return HttpResponse(status=403, content='Not administrator privileges, limited access')

        pageSize = Contants.PAGE_SIZE
        paginator = Paginator(tasks, pageSize)

        try:
            consumptionObjs = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            consumptionObjs = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            consumptionObjs = paginator.page(paginator.num_pages)

        # consumptions= Serializer().serialize(consumptionObjs,relations=('cpu',))
        consumptions = serialize(consumptionObjs)
        dict = json.loads(consumptions)
        for task in dict:
            cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
            task['config']['cpu'] = json.loads(serialize(cpus))
            sys = taskModels.System.objects.get(id=task['config']['sys'])
            task['config']['sys'] = model_to_dict(sys)

        data = {
            'tasks': json.dumps(dict),
            'page': page,
            'pageSize': pageSize,
            'total': paginator.count,
        }
    except Exception as e:
        logger.error(str(e))
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")
    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)


@login_required
def stateFilter(req):
    try:
        obJson = req.body
        data = json.loads(obJson)
        page = data.get('page')
        filter = data.get('filter')
        searchUserName = data.get('searchUserName')
        searchState = data.get('searchState')

        if filter == None or len(filter) == 0 or filter == '':
            if req.user.role == Contants.ROLE_ADMIN:
                tasks = taskModels.Task.objects.order_by('-time').all()

                if searchUserName != '' and not searchUserName:
                    tasks = tasks.filter(owner__username="{}".format(searchUserName))
                if searchState == 'normal':
                    tasks = tasks.filter(delete=0)
                elif searchState == 'delRow':
                    tasks = tasks.filter(delete=1)
                else:
                    pass

            else:
                # tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)
                # if searchUserName !=''  and not searchUserName:
                #     tasks=tasks.filter(owner__username="{}".format(searchUserName))
                # if searchState  == 'normal':
                #     tasks = tasks.filter(delete=0)
                # elif searchState == 'delRow':
                #     tasks = tasks.filter(delete=1)
                # else:
                #     pass
                return HttpResponse(status=403, content='Not administrator privileges, limited access')
        else:

            if not filter.has_key('kernel') and not filter.has_key('os') and not filter.has_key('cpu'):
                if req.user.role == Contants.ROLE_ADMIN:
                    tasks = taskModels.Task.objects.order_by('-time').all()
                else:
                    tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)
            else:
                if req.user.role == Contants.ROLE_ADMIN:
                    tasks = taskModels.Task.objects.order_by('-time').all()
                else:
                    tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

                if filter.has_key('cpu') and filter['cpu'] != '' and len(filter['cpu']) != 0:
                    cpus = filter['cpu']
                    cpuObjs = taskModels.Cpu.objects.filter(version__in=cpus)
                    tasks = tasks.filter(config_id__in=getCpuConfigId(cpuObjs))
                if filter.has_key('os') and filter['os'] != '' and len(filter['os']) != 0:
                    oss = filter['os']
                    configs = taskModels.Config.objects.filter(os__in=oss)
                    tasks = tasks.filter(config_id__in=getConfigId(configs))
                if filter.has_key('kernel') and filter['kernel'] != '' and len(filter['kernel']) != 0:
                    kernels = filter['kernel']
                    configs = taskModels.Config.objects.filter(kernel__in=kernels)
                    tasks = tasks.filter(config_id__in=getConfigId(configs))

        pageSize = Contants.PAGE_SIZE
        paginator = Paginator(tasks, pageSize)
        try:
            consumptionObjs = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            consumptionObjs = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            consumptionObjs = paginator.page(paginator.num_pages)

        # consumptions= Serializer().serialize(consumptionObjs,relations=('cpu',))
        consumptions = serialize(consumptionObjs)
        dict = json.loads(consumptions)
        for task in dict:
            cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
            task['config']['cpu'] = json.loads(serialize(cpus))
            sys = taskModels.System.objects.get(id=task['config']['sys'])
            task['config']['sys'] = model_to_dict(sys)

        data = {
            'tasks': json.dumps(dict),
            'page': page,
            'pageSize': pageSize,
            'total': paginator.count,
        }
    except Exception as e:
        logger.error(str(e))
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")
    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)


@login_required
def rowdelete(req):
    # from urllib import unquote
    # selection = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
    obJson = req.body
    data = json.loads(obJson)
    selection = json.loads(data.get('selection'))
    # print searchState
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

    for task in selection:
        tasks.filter(id=task['id']).update(delete=1)

    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok")


@login_required
def rowRestore(req):
    try:
        data = req.POST
        searchState = data.get('searchState')
        searchState = json.loads(searchState)

        # print searchState
        if req.user.role == Contants.ROLE_ADMIN:
            tasks = taskModels.Task.objects.order_by('-time').all()
        else:
            return HttpResponse(status=403, content='Not administrator privileges, limited access')

        # for i in range(len(searchState)):
        for selectTask in searchState:
            tasks.filter(id=selectTask['id']).update(delete=False)

    # tasks = tasks.filter(delete=1)
        pageSize = Contants.PAGE_SIZE
        paginator = Paginator(tasks, pageSize)
        try:
            consumptionObjs = paginator.page(1)
        except EmptyPage:
            consumptionObjs = paginator.page(paginator.num_pages)
        consumptions = serialize(consumptionObjs)
        dict = json.loads(consumptions)
        for task in dict:
            cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
            task['config']['cpu'] = json.loads(serialize(cpus))
            sys = taskModels.System.objects.get(id=task['config']['sys'])
            task['config']['sys'] = model_to_dict(sys)

            data = {
                'tasks': json.dumps(dict),
                'page': 1,
                'pageSize': pageSize,
                'total': paginator.count,
            }

    except Exception as e:
        logger.error(str(e))
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")
    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)


def delFiles(task):
    full_path = ''
    try:
        path = task['path']
        downloadPath = settings.uploadPath
        full_path = os.path.join(downloadPath, path) #压缩包路径

        base = os.path.basename(full_path)
        fileName,ext = os.path.splitext(base)
        parent_path = os.path.dirname(full_path)
        folder_path = os.path.join(parent_path,fileName)
        os.remove(full_path)
        import shutil
        shutil.rmtree(folder_path)
    except Exception as e:
        logger.debug("delete files exception:%s path is%s" % (str(e), full_path))



@login_required
def permanentDelete(req):
    try:
        data = req.POST
        searchState = data.get('searchState')
        searchState = json.loads(searchState)

        # print searchState
        if req.user.role == Contants.ROLE_ADMIN:
            tasks = taskModels.Task.objects.order_by('-time').all()
        else:
            return HttpResponse(status=403, content='Not administrator privileges, limited access')

        for selectTask in searchState:
            tasks.filter(id=selectTask['id']).delete()
            delFiles(selectTask)

        pageSize = Contants.PAGE_SIZE
        paginator = Paginator(tasks, pageSize)
        try:
            consumptionObjs = paginator.page(1)
        except EmptyPage:
            consumptionObjs = paginator.page(paginator.num_pages)
        consumptions = serialize(consumptionObjs)
        dict = json.loads(consumptions)
        for task in dict:
            cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
            task['config']['cpu'] = json.loads(serialize(cpus))
            sys = taskModels.System.objects.get(id=task['config']['sys'])
            task['config']['sys'] = model_to_dict(sys)

            data = {
                'tasks': json.dumps(dict),
                'page': 1,
                'pageSize': pageSize,
                'total': paginator.count,
            }

    except Exception as e:
        logger.error(str(e))
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")
    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)

def file_iterator(filename, chunk_size=512):
    with open(filename, "rb") as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break

def readFile(fn, buf_size=262144):#大文件下载，设定缓存大小
    f = open(fn, "rb")
    while True:#循环读取
        c = f.read(buf_size)
        if c:
            yield c
        else:
            break
    f.close()

@login_required
def downloadFile(req):

    obJson = req.body
    selection = json.loads(obJson)
    full_path = None
    real_path = None
    fileName = ''
    isMult = False #是否下载多个文件
    try:
        downloadPath = settings.uploadPath
        hasFile = False
        if len(selection) == 1:
            if os.path.exists(downloadPath):
                hasFile = True
                full_path = os.path.join(downloadPath, selection[0]['path'])
        else:
            zipName = str(uuid.uuid1()) + ".zip"

            full_path = os.path.join(downloadPath, TEMPFOLDER)
            if not os.path.exists(full_path):
                os.makedirs(full_path)
            full_path = os.path.join(full_path, zipName)
            import zipfile
            f = zipfile.ZipFile(full_path, 'w', zipfile.ZIP_DEFLATED)

            for s in selection:
                zip_path = os.path.join(downloadPath, s['path'])
                if os.path.exists(zip_path):
                    hasFile = True
                    fname = s['name'] + "-(" + str(s['id']) + ").zip"
                    print fname
                    f.write(zip_path,fname)
                    # f.write(zip_path,os.path.basename(zip_path))
            f.close()
        if full_path is not None and os.path.exists(full_path) and hasFile:
            splits = full_path.split("/")
            if len(selection) == 1:
                real_path = selection[0]['path']
                fileName = selection[0]['name']+"-("+str(selection[0]['id'])+").zip"
                isMult = False
            else:
                fileName = real_path = splits[len(splits) - 1]
                isMult = True
            if os.path.exists(full_path):
                return Response.CustomJsonResponse(Response.CODE_SUCCESS, 'ok',
                                                   {"path": real_path, "fileName": fileName, "isMult": isMult})
            else:
                return Response.CustomJsonResponse(Response.CODE_FAILED, 'fail')
            # response = FileResponse(open(full_path, 'rb'))
            # response['Content-Type'] = 'application/octet-stream'
            # response['Content-Disposition'] = 'attachment;filename="{0}"'.format(fileName)
            # response['fileName'] = fileName
            # return response
        # if full_path is not None and os.path.exists(full_path) and hasFile:
        #     splits = full_path.split("/")
        #     fileName = splits[len(splits) - 1]
        #     response = StreamingHttpResponse(file_iterator(full_path))
        #     response['Content-Type'] = 'application/octet-stream'
        #     response['Content-Disposition'] = 'attachment;filename="{0}"'.format(fileName)
        #     return response
    except Exception as e:
        logger.error(str(e))
    return Response.CustomJsonResponse(Response.CODE_FAILED, 'fail')

@login_required
def downloadReal(req):
    path = req.GET.get('path')
    fileName = req.GET.get('fileName')
    isMult = req.GET.get('isMult')
    downloadPath = settings.uploadPath
    logger.debug("isMult:%s", str(isMult))
    active = isMult == 'true'
    if active:
        full_path = os.path.join(downloadPath,TEMPFOLDER,path)
    else:
        full_path = os.path.join(downloadPath,path)
    logger.debug("fullPath:%s",full_path)
    response = StreamingHttpResponse(file_iterator(full_path))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(fileName)
    # response['fileName'] = fileName
    return response


    #
    #
    # downloadPath = settings.uploadPath
    #
    #
    #
    #
    #
    #
    # if req.method == 'GET':
    #     if req.user.role == Contants.ROLE_ADMIN:
    #         tasks = taskModels.Task.objects.order_by('-time').all()
    #     else:
    #         tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)
    #
    #     if downloadPath[-1] != '/': downloadPath = downloadPath + '/'
    #
    #     temp = tempfile.TemporaryFile()
    #     archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    #     flag = False
    #     for task in tasks:
    #         path = downloadPath + task.path
    #         if os.path.exists(path):
    #             flag = True
    #             filename = os.path.basename(path)
    #             archive.write(path, filename)
    #     archive.close()
    #
    #     if not flag:
    #         return HttpResponse(status=404, content='not found')
    #     wrapper = FileWrapper(temp)
    #
    #     size = temp.tell()
    #     temp.seek(0)
    #     response = HttpResponse(wrapper, content_type='application/octet-stream')
    #     response['Content-Disposition'] = 'attachment;filename="{0}"'.format('{}.zip'.format(req.user))
    #     response['Content-Length'] = size
    #     return response
    #     # return HttpResponse(status=200)
    # else:
    #     return HttpResponse(status=403)


def parseTableCols(model):
    # taskModels.Cpu._meta.fields[0].attname
    cols = []
    for field in model._meta.fields:
        if field.name != 'id' and field.name != 'config':
            print field.name
            col = {
                'title': str(field.name).upper(),
                'key': field.name,
                'align': 'center',
            }
            cols.append(col)
    return cols


def parseTableCols_partitions():
    # taskModels.Cpu._meta.fields[0].attname
    cols = []
    first_col = {
        'title': 'Partition DeviceName',
        'key': 'devicename',
        'align': 'center',
    }
    cols.append(first_col)
    for field in taskModels.Partition._meta.fields:
        if field.name != 'id' and field.name != 'config' and field.name != 'storage':
            print field.name
            col = {
                'title': str(field.name).upper(),
                'key': field.name,
                'align': 'center',
            }
            cols.append(col)
    return cols


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


@login_required
def singleTask(req):
    from urllib import unquote
    taskIds = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
    task = taskModels.Task.objects.filter(id=taskIds[0]).first()
    # task = model_to_dict(task)
    dims = taskModels.Dimension.objects.all()
    dimObjs = serialize(dims)

    cpus = taskModels.Cpu.objects.filter(config_id=task.config.id)
    board = taskModels.Config.objects.get(id=task.config.id).board
    sys = taskModels.Config.objects.get(id=task.config.id).sys
    caches = taskModels.Cache.objects.filter(config_id=task.config.id)
    memorys = taskModels.Memory.objects.filter(config_id=task.config.id)
    nets = taskModels.Net.objects.filter(config_id=task.config.id).\
        exclude(address__isnull=True,netmask__isnull=True).\
        exclude(address__exact='',netmask__exact='') #Network information中没有IP&NERMASK的网口不进行展示
    storages = taskModels.Storage.objects.filter(config_id=task.config.id)
    storages = json.loads(serialize(storages))
    partitions = []
    for storage in storages:
        partitions = taskModels.Partition.objects.filter(storage_id=storage['id'])
        partitions = json.loads(serialize(partitions))
        for p in partitions:
            p['devicename'] = storage['devicename']
            # storage['partitions'] = json.loads(partition)
    syss = []
    syss.append(model_to_dict(sys))
    boards = []
    boards.append(model_to_dict(board))

    # logs = taskModels.Log.objects.filter(task_id = task['id']) #所有的测试工具的日志
    #
    # logs = serialize(logs)

    cursor = connection.cursor()

    try:
        sql = "SELECT a.name as dimName, d.name as toolName, e.content FROM dimResult as dim " \
              "LEFT JOIN  dimension AS a on  dim.dim_id = a.id " \
              "LEFT JOIN scenario AS b ON a.id = b.dim_id " \
              "LEFT JOIN testCase AS c ON b.id = c.scenario_id " \
              "LEFT JOIN testTool AS d ON c.tool_id = d.id " \
              "LEFT JOIN log AS e ON d.id = e.tool_id and e.task_id = %s " \
              "where dim.task_id= %s " \
              "GROUP BY a.`name`,d.name";
        print  sql
        cursor.execute(sql, [task.id, task.id])
        datas = dictfetchall(cursor)

    finally:
        cursor.close()
    dimResults = taskModels.DimResult.objects.filter(task_id=task.id)
    dimResults = json.loads(serialize(dimResults))
    for dimResult in dimResults:
        tools = []
        for data in datas:
            if dimResult['dim']['name'] == data['dimName']:
                tool = {
                    "name": data['toolName'],
                    "content": data['content']
                }
                tools.append(tool)
        dimResult['dim']['name'] = str(dimResult['dim']['name']).upper()
        dimResult['tools'] = tools
    data = {
        'dims': dimObjs,
        'cpu_cols': json.dumps(parseTableCols(taskModels.Cpu)),
        'cpus': serialize(cpus),
        'board_cols': json.dumps(parseTableCols(taskModels.Baseboard)),
        'board': json.dumps(boards),
        'sys_cols': json.dumps(parseTableCols(taskModels.System)),
        'sys': json.dumps(syss),
        'cache_cols': json.dumps(parseTableCols(taskModels.Cache)),
        'caches': serialize(caches),
        'memory_cols': json.dumps(parseTableCols(taskModels.Memory)),
        'memorys': serialize(memorys),
        'net_cols': json.dumps(parseTableCols(taskModels.Net)),
        'nets': serialize(nets),
        'storage_cols': json.dumps(parseTableCols(taskModels.Storage)),
        'storages': json.dumps(storages),
        'partition_cols': json.dumps(parseTableCols_partitions()),
        'partitions': json.dumps(partitions),
        'dim_tools': dimResults,
        'isShowBack': True,
        'remark': task.remark
    }
    return render(req, "singleTask.html", data)


def tool_result(request, toolName):
    print toolName
    toolName = str(toolName).lower()
    content = []
    try:
        from urllib import unquote
        taskIds = json.loads(unquote(request.COOKIES.get("selection")))  # 选中的task 任务
        id = taskIds[0]
        log = taskModels.Log.objects.get(tool__name=toolName,task_id=id)
        content = log.content
    except:
        content = []
    try:
        if type(content) == str or type(content) == unicode:
            content = json.loads(content)
    except:
        content = []
    return render(request, 'tool.html', {"toolName": toolName, "content": content, 'isShowBack': True})


def showtree(rootDir):
    # result_dirs=[]
    result_files = []
    list_dirs = os.walk(rootDir)
    for root, dirs, files in list_dirs:
        '''
        for d in dirs: 
            dirpath=os.path.join(root, d)
            result_dirs.append(dirpath.split("output\\")[1])    
        '''
        for f in files:
            filepath = os.path.join(root, f)
            if filepath.endswith("_json.txt"):
                toolName = os.path.basename(filepath).split("_")[0]
                tools = {"toolName": toolName, "logPath": filepath}
                result_files.append(tools)
    return result_files


@login_required
def folder(req, taskId):
    try:
        import CaliperServer.settings as s
        task = taskModels.Task.objects.get(id=taskId)
        filepath, outputShotname, extension = Utils.get_filePath_fileName_fileExt(task.path)
        print outputShotname
        folderPath = os.path.join(s.uploadPath, outputShotname)

        print "--------------------------------------"
        datas = gci(folderPath)
        data = {
            "datas": json.dumps(datas),
            'isShowBack': True
        }
    except Exception as e:
        logger.error('can not found task')
        data = {
            "datas": [],
            'isShowBack': True
        }
    return render(req, 'folder.html', data)


def gci(path):
    """this is a statement"""
    datas = []
    parents = os.listdir(path)
    for parent in parents:
        child = os.path.join(path, parent)
        # print(child)

        if os.path.isdir(child):
            data = {
                "title": parent,
                "expand": True,
                "children": gci(child)
            }

            datas.append(data)
        # print(child)
        else:
            data = {
                "title": parent,
                "content": open(child, 'r').read()
            }
            datas.append(data)
    return datas


@login_required
def userList(req):
    # if not  req.POST:
    #     return HttpResponse(status=403)
    obJson = req.body

    if obJson != '' and json.loads(obJson).has_key('page'):
        page = json.loads(obJson)['page']
    else:
        page = 1

    from urllib import unquote
    taskIds = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
    if taskIds is None:
        return HttpResponse(status=403)

    if len(taskIds) > 1:
        return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", {})
    else:

        id = taskIds[0]
        task = taskModels.Task.objects.get(id=id)

        sl = task.shareusers.order_by('id').all()

        # print  share_data
        pageSize = Contants.PAGE_SIZE

        paginator = Paginator(sl, pageSize)
        try:
            consumptionObjs = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            consumptionObjs = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            consumptionObjs = paginator.page(paginator.num_pages)

        # consumptions= Serializer().serialize(consumptionObjs,relations=('cpu',))
        share_data = []
        for i in range(len(consumptionObjs)):
            temp = {}
            temp['userName'] = consumptionObjs[i].username
            temp['userID'] = consumptionObjs[i].id
            temp['taskId'] = task.id
            share_data.append(temp)

        data = {
            'usercounts': paginator.count,
            'taskName': task.config.hostname + "(" +str(task.id) + ")",
            'data1': share_data,
            'page': page,
            'pageSize': pageSize,
            'total': paginator.count,
        }

    return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)
    # return HttpResponse(status=200,content='{}')


@login_required
def addUserSubmit(req):
    try:
        data = req.body
        data = json.loads(data)
        usernames = data['usernames']
        selection = data['selection']
        if usernames == None or selection == None:
            return Response.CustomJsonResponse(Response.CODE_SUCCESS, 'miss',)
        usernames = [x.strip() for x in usernames.split(',')]
        if req.user.username in usernames:
            return Response.CustomJsonResponse(Response.CODE_FAILED, 'self')
        users = taskModels.UserProfile.objects.filter(username__in=usernames,role=Contants.ROLE_USER)
        if users is None or users.count() == 0:
            return Response.CustomJsonResponse(Response.CODE_FAILED, 'no')
        elif users.count() < len(usernames):
            return Response.CustomJsonResponse(Response.CODE_FAILED, 'hasno') #多个用户时,有部分不存在
        for user in users:
            for task in selection:
                taskModel = taskModels.Task.objects.get(id=task['id'])
                exist = taskModel.shareusers.filter(id=user.id).exists()
                if not exist:
                    taskModel.shareusers.add(user)
                    taskModel.save()

        # if len(failUsers) > 0:
        #     failMsg =''
        #     for index,failUser in failUsers:
        #         if index == len(failUsers)-1:
        #             failMsg = failMsg + failUser
        #         else:
        #             failMsg = failMsg+failUser+","
        #     return Response.CustomJsonResponse(Response.CODE_SUCCESS, 'exist',failMsg)
        # for task in selection:
        #     taskModel = taskModels.Task.objects.get(id=task['id'])
        #     for user in users:
        #         taskModel.shareusers.add(user)
        #         taskModel.save()
        return Response.CustomJsonResponse(Response.CODE_SUCCESS, 'ok')

        # for i in range(len(usernames)):
        #
        #     try:
        #         user = taskModels.UserProfile.objects.get(username=usernames[i])
        #         users.append(user)
        #
        #     except:
        #         logger.error("user is not found")
        #         failAdd.append(usernames[i])

        # for task in selection:
        #     try:
        #         taskModel = taskModels.Task.objects.get(id=task['id'])
        #         taskModel.shareusers
        #         for user in users:
        #             taskModel.shareusers.add(user)
        #             taskModel.save()
        #     except:
        #         logger.error('task is not found')
        # return HttpResponse(status=200)
        # print failAdd
        # print users

    except Exception as e:
        logger.debug(str(e))
        return Response.CustomJsonResponse(Response.CODE_SUCCESS, 'fail')


@login_required
def addUser(req):
    if req.method != 'POST':
        return HttpResponse(status=403)
    data = req.POST
    searchState = data.get('searchState')
    if searchState is None:
        return HttpResponse(status=403)
    selection = json.loads(searchState)

    data = {
        'usercounts': len(selection[0]['shareusers']),
        'machinaryCode': selection[0]['id'],
    }
    return Response.CustomJsonResponse(Response.CODE_SUCCESS, 'ok', data)


@login_required
def delete(req):
    obJson = req.body
    userId = 0
    taskId = 0
    if obJson != '':
        if json.loads(obJson).has_key('userId'):
            userId = json.loads(obJson)['userId']
        if json.loads(obJson).has_key('taskId'):
            taskId = json.loads(obJson)['taskId']
    if userId == 0 or taskId == 0:
        return Response.CustomJsonResponse(Response.CODE_FAILED, 'fail')
    else:
        try:
            task = taskModels.Task.objects.get(id=taskId)
            user = userModels.UserProfile.objects.get(id=userId)
            task.shareusers.remove(user)
            task.save()
            return Response.CustomJsonResponse(Response.CODE_SUCCESS, 'ok')
        except:
            return Response.CustomJsonResponse(Response.CODE_FAILED, 'fail')


@login_required
def deleteAll(req):
    obJson = req.body
    taskId = 0
    if obJson != '':
        if json.loads(obJson).has_key('taskId'):
            taskId = json.loads(obJson)['taskId']
    if taskId == 0:
        return Response.CustomJsonResponse(Response.CODE_FAILED, 'fail')
    else:
        try:

            task = taskModels.Task.objects.get(id=taskId)
            task.shareusers.clear()
            task.save()
            return Response.CustomJsonResponse(Response.CODE_SUCCESS, 'ok')
        except:
            return Response.CustomJsonResponse(Response.CODE_FAILED, 'fail')
