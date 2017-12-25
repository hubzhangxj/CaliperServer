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
        obJson = req.POST
        selection = json.loads(unquote(req.COOKIES.get("selection")))  # 选中的task 任务
        size = len(selection)
        dims = taskModels.Dimension.objects.all()

        # 蛛网图 数据构造  start
        categories = []
        series_data = []
        for index, task in enumerate(selection):
            data = []
            for dim in dims:
                categories.append(dim.name)
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=task['id'], dim_id=dim.id)
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

        for index, dim in enumerate(dims):
            data = []
            for task in selection:
                try:
                    dimResult = taskModels.DimResult.objects.get(task_id=task['id'], dim_id=dim.id)
                    data.append(dimResult.result)
                except:
                    logger.error('find dimresult none')
                    data.append(0)

            single = {
                'name': dim.name,
                'data': data,
                'visible': index == 0
                # 'pointPlacement': 'on'
            }
            lineSeries.append(single)

        print lineSeries
        # 折线图 数据构造  end

        # table 数据构造  start
        columns = []  #table column 配置
        firstCol = {
            'title': 'platform',
            'key': 'os',
            'align': 'center',
        }
        secondCOl ={
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
        tableData = [] #table column 对应的数据值
        for task in selection:
            tableSingle={}
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


        for index,td in enumerate(tableData):
            if index !=0:
                cellClassName = {}
                for key,value in td.items():
                    if key == 'os' or key =='time':
                        continue
                    firstValue = tableData[0][key]
                    if value > firstValue * 1.05:
                        cellClassName[key]= 'table-info-row-green'
                        print '绿色'
                    elif value < firstValue * 0.95:
                        cellClassName[key] = 'table-info-row-red'
                        print '红色'
                    else:
                        print '正常'
                        cellClassName[key] = 'table-info-row-black'
                td['cellClassName'] = cellClassName

        # table 数据构造  end
        data = {
            'categories': json.dumps(categories),
            'series': json.dumps(series_data),
            'lineSeries': json.dumps(lineSeries),
            'times': json.dumps(times),
            'isSame':isSame(selection), #是否同一个系统平台
            'columns':json.dumps(columns),
            'tableData':json.dumps(tableData)
        }
    except Exception as e:
        logger.error(str(e))
        return render(req, "compare.html", {})
    return render(req, "compare.html", data)


def isSame(data):
    n = len(data)
    isSame = True
    for i in range(0, n):
        for j in range(i + 1, n):
            if (data[i]['config']['os'] != data[j]['config']['os']):
                isSame = False
                break

    return isSame
