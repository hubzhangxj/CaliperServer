# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import QuerySet
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
    os_list=[]
    cpu_list=[]
    kernel_list=[]
    for osObj in oss:
        os = {
            "id":osObj.os,
            "text":osObj.os
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

    tableData = []  # table column 对应的数据值

    for sce in sces:
        tableSingle = {}
        tableSingle['name'] = sce.name
        for task in selection:
            try:
                dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=task['id'])
                sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario_id=sce.id)
                tableSingle[task['id']] = sceResult.result

            except:
                tableSingle[task['id']] = 0
        tableData.append(tableSingle)
    tableData = highlight2(tableData, selection[0]['id'], ['name'])
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
            for task in selection:
                try:
                    dimResult = taskModels.DimResult.objects.get(dim__name=param, task_id=task['id'])
                    sceResult = taskModels.ScenarioResult.objects.get(dimresult_id=dimResult.id, scenario__name=scename)
                    caseResult = taskModels.CaseResult.objects.get(sceResult_id=sceResult.id, case__name=casename)
                    tableSingle[task['id']] = caseResult.result

                except:
                    tableSingle[task['id']] = 0
            case_table_data.append(tableSingle)
        sce_table_data[scename] = highlight2(case_table_data, selection[0]['id'], ['name'])

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


def highlight(tableData, exclude=[]):
    for index, td in enumerate(tableData):
        if index != 0:
            cellClassName = {}
            for key, value in td.items():
                if key in exclude:
                    continue
                firstValue = tableData[0][key]
                if value > firstValue * 1.05:
                    cellClassName[key] = 'table-info-row-green'
                    print '绿色'
                elif value < firstValue * 0.95:
                    cellClassName[key] = 'table-info-row-red'
                    print '红色'
                else:
                    print '正常'
                    cellClassName[key] = 'table-info-row-black'
            td['cellClassName'] = cellClassName
    return tableData


def highlight2(tableData, compareKey, exclude=[]):
    '''
    左右 去对比是否高亮
    :param tableData:
    :param exclude:
    :return:
    '''
    for index, td in enumerate(tableData):
        cellClassName = {}
        for key, value in td.items():
            if key in exclude or key == compareKey:
                continue
            firstValue = td[compareKey]
            if value > firstValue * 1.05:
                cellClassName[key] = 'table-info-row-green'
                print '绿色'
            elif value < firstValue * 0.95:
                cellClassName[key] = 'table-info-row-red'
                print '红色'
            else:
                print '正常'
                cellClassName[key] = 'table-info-row-black'
        td['cellClassName'] = cellClassName
    return tableData


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
    #print consumptionObjs.object_list
    return render(req, "boardInfo.html", data)
def stateSearchUser(req):
    if not  req.POST:
        return HttpResponse(status=403)
    data=req.POST
    searchUserName = data.get('searchUserName')
    searchState = data.get('searchState')
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)
    if searchUserName:
        tasks=tasks.filter(owner__username=searchUserName)
    if searchState == "delRow":
        tasks=tasks.filter(delete=1)
    elif  searchState == "normal":
        tasks = tasks.filter(delete=0)
    else:
        pass
    try:
        if not  tasks:
            print tasks
            return HttpResponse(status=404,data={'tasks':'','page':1,'pageSize':1,'total':1})
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
                return HttpResponse(status=404, data={'tasks': '', 'page': 1, 'pageSize': 1, 'total': 1})
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
        if not  tasks:
            return HttpResponse(status=404,data={'tasks':'','page':1,'pageSize':1,'total':1})
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
    if not  req.POST:
        return HttpResponse(status=403)
    data=req.POST
    searchState = data.get('searchState')
    searchState = json.loads(searchState)

    #print searchState
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

    for i in range(len(searchState)):

        tasks.filter(config_id=searchState[i]['id']).update(delete=1)


    tasks=tasks.filter(delete=0)
    try:
        if not  tasks:
            print tasks
            return HttpResponse(status=404,data={'tasks':'','page':1,'pageSize':1,'total':1})
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
    if not  req.POST:
        return HttpResponse(status=403)
    data=req.POST
    searchState = data.get('searchState')
    searchState = json.loads(searchState)

    #print searchState
    if req.user.role == Contants.ROLE_ADMIN:
        tasks = taskModels.Task.objects.order_by('-time').all()
    else:
        tasks = taskModels.Task.objects.order_by('-time').filter(owner_id=req.user.id)

    for i in range(len(searchState)):

        tasks.filter(config_id=searchState[i]['id']).update(delete=0)

    tasks = tasks.filter(delete=1)
    try:
        if not  tasks:
            print tasks
            return HttpResponse(status=404,data={'tasks':'','page':1,'pageSize':1,'total':1})
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