# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import connection
from django.shortcuts import render
from task import models as taskModels
from shared.serializers.json import Serializer, DjangoJSONEncoder
import json
from shared import Contants
from shared.serializers.serialize_json import model_to_dict
from shared.Response import Response
from shared.log import logger
# Create your views here.
from django.http import StreamingHttpResponse, HttpResponse, HttpResponseRedirect


def serialize(data, excluded='avatar'):
    return Serializer().serialize(data, excluded=excluded)


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
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

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
    }
    print consumptionObjs.object_list
    print "============="
    return render(req, "task.html", data)


def pageChange(req):
    try:
        obJson = req.body
        # params = json.loads(obJson)
        if obJson != '' and json.loads(obJson).has_key('page'):
            page = json.loads(obJson)['page']
        else:
            page = 1

        if req.user.role == Contants.ROLE_ADMIN:
            tasks = taskModels.Task.objects.order_by('-time').all()
        else:
            tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

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


def filter(req):
    try:
        obJson = req.body
        page = json.loads(obJson)['page']
        filter = json.loads(obJson)['filter']
        if filter == None or len(filter) == 0 or filter == '':
            if req.user.role == Contants.ROLE_ADMIN:
                tasks = taskModels.Task.objects.order_by('-time').all()
            else:
                tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)
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


def compare(req):
    try:
        from urllib import unquote
        # obJson = req.POST
        selection = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
        size = len(selection)
        categories = []
        dims = taskModels.Dimension.objects.all()
        for dim in dims:
            categories.append(dim.name)

        # 蛛网图 数据构造  start

        series_data = []
        for index, task in enumerate(selection):
            data = []
            for categorie in categories:
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=task['id'], dim__name=categorie)
                    data.append(dimResult.result)
                except:
                    logger.error('find dimresult none')
                    data.append(0)

            single = {
                'name': task['name'],
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

        for task in selection:
            times.append(task['time'])

        for index, categorie in enumerate(categories):
            data = []
            for task in selection:
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=task['id'], dim__name=categorie)
                    data.append(dimResult.result)
                except:
                    logger.error('find dimresult none')
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
        tableData = []  # table column 对应的数据值
        for task in selection:
            tableSingle = {}
            tableSingle['os'] = task['config']['os']
            tableSingle['time'] = task['time']
            for dim in dims:
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=task['id'], dim_id=dim.id)
                    tableSingle[dim.name] = dimResult.result
                except:
                    logger.error('find dimresult none')
                    tableSingle[dim.name] = 0
            tableData.append(tableSingle)
        print tableSingle

        tableData = highlight(tableData, ['os', 'time'])

        # table 数据构造  end
        data = {
            'categories': json.dumps(categories),
            'series': json.dumps(series_data),
            'lineSeries': json.dumps(lineSeries),
            'times': json.dumps(times),
            'isSame': isSame(selection),  # 是否同一个系统平台
            'columns': json.dumps(columns),
            'tableData': json.dumps(tableData)
        }
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
    import numpy as np
    if type(values) == list and 0 not in values:
        return np.var(values)
    else:
        return 0


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
    selection = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
    sce_series = []
    for task in selection:
        data = []
        try:
            dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=task['id'])
            for categorie in categories:
                try:
                    sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id,
                                                                      scenario__name=categorie)
                    data.append(sceResult.result)
                except:
                    data.append(0)
        except:
            data = []

        single = {
            'name': task['name'],
            'data': data,
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
    for task in selection:
        singleCol = {
            'title': task['name'],
            'key': task['id'],
            'align': 'center',
        }
        columns.append(singleCol)
    endCol = {
        'title': 'variance', #方差
        'key': 'variance',
        'align': 'center',
    }
    columns.append(endCol)
    tableData = []  # table column 对应的数据值

    for sce in sces:
        tableSingle = {}
        tableSingle['name'] = sce.name
        values = []
        for task in selection:
            try:
                dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=task['id'])
                sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario_id=sce.id)
                tableSingle[task['id']] = sceResult.result
                values.append(sceResult.result)
            except:
                tableSingle[task['id']] = 0
                values.append(0)
        tableSingle['variance'] = variance(values)
        tableData.append(tableSingle)
    tableData = highlight2(tableData, selection[0]['id'], ['name','variance'])
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

    case_series = {}
    for scename, values in case_categories.items():  # 场景的集合
        task_case_data = []
        for task in selection:  # 选择的任务的集合
            case_data = []
            for casename in values:  # case名称的集合
                try:
                    dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=task['id'])
                    sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario__name=scename)
                    caseResult = taskModels.CaseResult.objects.get(sceResult_id=sceResult.id, case__name=casename)
                    case_data.append(caseResult.result)
                except:
                    case_data.append(0)

            case_signle = {
                'name': task['name'],
                'data': case_data,
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

    sce_table_data = {}
    for scename, values in case_categories.items():  # 场景的集合
        case_table_data = []
        for casename in values:  # case名称的集合
            tableSingle = {}
            tableSingle['name'] = casename
            values = []
            for task in selection:
                try:
                    dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=task['id'])
                    sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario__name=scename)
                    caseResult = taskModels.CaseResult.objects.get(sceResult_id=sceResult.id, case__name=casename)
                    tableSingle[task['id']] = caseResult.result
                    values.append(caseResult.result)
                except:
                    tableSingle[task['id']] = 0
                    values.append(0)
            tableSingle['variance'] = variance(values)
            case_table_data.append(tableSingle)
        sce_table_data[scename] = highlight2(case_table_data, selection[0]['id'], ['name','variance'])

    # table 数据构造  end




    data = {
        'categories': json.dumps(categories),
        'param': param,
        'sce_series': json.dumps(sce_series),
        'columns': json.dumps(columns),
        'tableData': json.dumps(tableData),
        # 'case_categories':json.dumps(case_categories),
        'case_series': json.dumps(case_series),
        'sce_table_data': json.dumps(sce_table_data)
    }
    return render(req, "dimcompare.html", data)


def highlight(tableData, exclude=[],hl=5):
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
                elif value < firstValue -hl:
                    cellClassName[key] = 'table-info-row-red'
                    print '红色'
                else:
                    print '正常'
                    cellClassName[key] = 'table-info-row-black'
            td['cellClassName'] = cellClassName
    return tableData


def highlight2(tableData, compareKey,  exclude=[],hl=5):
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


def highlightChange(req):
    obJson = req.body
    if obJson is not  None and obJson !="":
        obj = json.loads(obJson)
        hl = obj['highlight']
        tableData = json.loads(obj['tableData'])
        from urllib import unquote
        selection = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
        tableData = highlight2(tableData,str(selection[0]['id']),['name','variance','cellClassName'],hl)
        data={
            "tableData": tableData
        }
        return Response.CustomJsonResponse(Response.CODE_SUCCESS, "ok", data)
    else:
        return Response.CustomJsonResponse(Response.CODE_FAILED, "fail")


def isSame(data):
    n = len(data)
    isSame = True
    for i in range(0, n):
        for j in range(i + 1, n):
            if (data[i]['config']['os'] != data[j]['config']['os']):
                isSame = False
                break

    return isSame


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
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

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
    }
    print data['total']
    # print consumptionObjs.object_list
    return render(req, "boardInfo.html", data)


def stateSearchUser(req):
    if not req.POST:
        return HttpResponse(status=403)
    data = req.POST
    searchUserName = data.get('searchUserName')
    searchState = data.get('searchState')
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)
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


def statePageChange(req):
    try:
        obJson = req.body
        # params = json.loads(obJson)
        if obJson != '' and json.loads(obJson).has_key('page'):
            page = json.loads(obJson)['page']
        else:
            page = 1
        searchUserName = json.loads(obJson)['searchUserName']
        searchState = json.loads(obJson)['searchState']

        if req.user.role == Contants.ROLE_ADMIN:
            tasks = taskModels.Task.objects.order_by('-time').all()
        else:
            tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

        if searchUserName:
            tasks = tasks.filter(owner__username=searchUserName)

        if searchState == "delRow":
            tasks = tasks.filter(delete=1)
        elif searchState == "normal":
            tasks = tasks.filter(delete=0)

        #
        # if req.user.role == Contants.ROLE_ADMIN:
        #     tasks = taskModels.Task.objects.order_by('-time').all()
        # else:
        #     tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

        pageSize = Contants.PAGE_SIZE
        paginator = Paginator(tasks, pageSize)

        try:
            if not tasks:
                return HttpResponse(status=404)
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


def stateFilter(req):
    try:
        obJson = req.body
        page = json.loads(obJson)['page']
        filter = json.loads(obJson)['filter']
        searchUserName = json.loads(obJson)['searchUserName']
        searchState = json.loads(obJson)['searchState']
        cmd = '''tasks = taskModels.Task.objects'''

        if filter == None or len(filter) == 0 or filter == '':
            if req.user.role == Contants.ROLE_ADMIN:
                tasks = taskModels.Task.objects.order_by('-time').all()
            else:
                tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

            if searchUserName:
                tasks = tasks.filter(owner__username=searchUserName)

            if searchState == "delRow":
                tasks = tasks.filter(delete=1)
            elif searchState == "normal":
                tasks = tasks.filter(delete=0)
        else:

            if not filter.has_key('kernel') and not filter.has_key('os') and not filter.has_key('cpu'):
                if req.user.role == Contants.ROLE_ADMIN:
                    tasks = taskModels.Task.objects.order_by('-time').all()
                else:
                    tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

                if searchUserName:
                    tasks = tasks.filter(owner__username=searchUserName)

                if searchState == "delRow":
                    tasks = tasks.filter(delete=1)
                elif searchState == "normal":
                    tasks = tasks.filter(delete=0)
            else:
                if req.user.role == Contants.ROLE_ADMIN:
                    tasks = taskModels.Task.objects.order_by('-time').all()
                else:
                    tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

                if searchUserName:
                    tasks = tasks.filter(owner__username=searchUserName)

                if searchState == "delRow":
                    tasks = tasks.filter(delete=1)
                elif searchState == "normal":
                    tasks = tasks.filter(delete=0)

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
        if not tasks:
            return HttpResponse(status=404)
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


def rowdelete(req):
    if not req.POST:
        return HttpResponse(status=403)
    data = req.POST
    searchState = data.get('searchState')
    searchState = json.loads(searchState)

    # print searchState
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

    for i in range(len(searchState)):
        tasks.filter(config_id=searchState[i]['id']).update(delete=1)

    tasks = tasks.filter(delete=0)
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


def rowRestore(req):
    if not req.POST:
        return HttpResponse(status=403)
    data = req.POST
    searchState = data.get('searchState')
    searchState = json.loads(searchState)

    # print searchState
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

    for i in range(len(searchState)):
        tasks.filter(config_id=searchState[i]['id']).update(delete=0)

    tasks = tasks.filter(delete=1)
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


def permanentDelete(req):
    if not req.POST:
        return HttpResponse(status=403)
    data = req.POST
    searchState = data.get('searchState')
    searchState = json.loads(searchState)

    # print searchState
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

    for i in range(len(searchState)):
        tasks.filter(config_id=searchState[i]['id']).delete()

    tasks = tasks.filter(delete=0)
    try:
        if not tasks:
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


def downloadFile(req):
    import CaliperServer.settings as settings
    import os, tempfile, zipfile
    from wsgiref.util import FileWrapper
    downloadPath = settings.downloadPath
    if req.method == 'GET':
        if req.user.role == Contants.ROLE_ADMIN:
            tasks = taskModels.Task.objects.order_by('-time').all()
        else:
            tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

        if downloadPath[-1] != '/': downloadPath = downloadPath + '/'

        temp = tempfile.TemporaryFile()
        archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
        flag = False
        for task in tasks:
            path = downloadPath + task.path
            if os.path.exists(path):
                flag = True
                filename = os.path.basename(path)
                archive.write(path, filename)
        archive.close()

        if not flag:
            return HttpResponse(status=404, content='not found')
        wrapper = FileWrapper(temp)

        size = temp.tell()
        temp.seek(0)
        response = HttpResponse(wrapper, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format('{}.zip'.format(req.user))
        response['Content-Length'] = size
        return response
        # return HttpResponse(status=200)
    else:
        return HttpResponse(status=403)


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


def singleTask(req):
    from urllib import unquote
    selection = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
    task = selection[0]

    dims = taskModels.Dimension.objects.all()
    dimObjs = serialize(dims)

    cpus = taskModels.Cpu.objects.filter(config_id=task['config']['id'])
    board = taskModels.Config.objects.get(id=task['config']['id']).board
    sys = taskModels.Config.objects.get(id=task['config']['id']).sys
    caches = taskModels.Cache.objects.filter(config_id=task['config']['id'])
    memorys = taskModels.Memory.objects.filter(config_id=task['config']['id'])
    nets = taskModels.Net.objects.filter(config_id=task['config']['id'])
    storages = taskModels.Storage.objects.filter(config_id=task['config']['id'])
    storages = json.loads(serialize(storages))
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
        sql = "SELECT a.name as dimName, d.name as toolName, e.content FROM dimension AS a " \
              "LEFT JOIN scenario AS b ON a.id = b.dim_id " \
              "LEFT JOIN testCase AS c ON b.id = c.scenario_id " \
              "LEFT JOIN testTool AS d ON c.tool_id = d.id " \
              "LEFT JOIN log AS e ON d.id = e.tool_id " \
              "GROUP BY a.`name`,d.name";
        print  sql
        cursor.execute(sql)
        datas = dictfetchall(cursor)

    finally:
        cursor.close()
    dimResults = taskModels.DimResult.objects.filter(task_id=task['id'])
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

        # dimResults = taskModels.DimResult.objects.filter(task_id= task['id'])
        # dim_tools=[]
        # for dimResult in dimResults:
        #     sces = taskModels.Scenario.objects.filter(dim_id = dimResult.dim_id)
        #     tools = []
        #     for sce in sces:
        #         cases = taskModels.TestCase.objects.filter(scenario_id = sce.id)
        #         for case in cases:
        #             log = taskModels.Log.objects.get(task_id=task['id'],tool_id=case.tool.id)
        #             tool = model_to_dict(case.tool)
        #             tool['log'] =  model_to_dict(log)
        #             tools.append(tool)
        #     dict = {
        #         "dim": dimResult.dim.name,
        #         "tools": tools
        #     }
        #     dim_tools.append(dict)
        # sceResults = taskModels.ScenarioResult.objects.filter(dimresult_id = dimResult.id)
        # for sceResult in sceResults:
        #     caseResults = taskModels.CaseResult.objects.filter(sceResult_id=sceResult.id)

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
        'dim_tools': dimResults
    }
    return render(req, "singleTask.html", data)


def tool_result(request, toolName):
    print toolName
    toolName = str(toolName).lower()
    content = []
    try:
        log = taskModels.Log.objects.get(tool__name=toolName)
        content = log.content
    except:
        content = []
    try:
        if type(content) == str or type(content) == unicode:
            content = json.loads(content)
    except:
        content = []
    return render(request, 'tool.html', {"toolName": toolName, "content": content})
