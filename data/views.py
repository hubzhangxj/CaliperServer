# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
import json, os, uuid, zipfile, subprocess
from shared import Utils
from CaliperServer import settings
from shared.Response import Response
from django.http import HttpResponse
from shared.log import logger
from task import models as taskModels
from account import models as accountModels
from django.db import transaction

PASSWORD = '123'
CONFIG_FILENAME = "hardwareinfo.json"


@csrf_exempt
def upload(request):
    '''
    上传数据接口，有2个文件参数，4个文本参数
    原始的数据压缩包: output
    解析过得工具日志压缩包: log
    用户名：username
    得分json：result
    原始的数据压缩包Hash值: hash_output
    解析过得工具日志压缩包:hash_log
    '''
    print "============"
    if request.method == "POST":
        print "------------------"
        if "output" in request.FILES and "log" in request.FILES:
            # outputFile = request.FILES.get("output", None)
            outputFile = request.FILES["output"]
            logFile = request.FILES.get("log", None)
            username = request.POST['username']
            result = request.POST['result']
            rDict = json.loads(result)
            print rDict
            hash_output = request.POST['hash_output']
            hash_log = request.POST['hash_log']
            outputFileName = str(uuid.uuid1())
            logFileName = str(uuid.uuid1())
            output_path = os.path.join(settings.uploadPath, outputFileName + ".zip")
            log_path = os.path.join(settings.uploadPath, logFileName + ".zip")
            handle_uploaded_file(outputFile, output_path)
            handle_uploaded_file(logFile, log_path)

            realOutputHash = Utils.calcHash(output_path)
            realLogHash = Utils.calcHash(log_path)

            if hash_output != realOutputHash or hash_log != realLogHash:  # 废弃 这次任务
                os.remove(output_path)
                os.remove(log_path)
                return HttpResponse(status=400)
            else:  # 存储数据库，解析文件

                filepath, outputShotname, extension = Utils.get_filePath_fileName_fileExt(output_path)
                print outputShotname
                sourceDir_output = os.path.join(settings.uploadPath, outputShotname)
                decryptZip(output_path, sourceDir_output)

                make_zip(sourceDir_output, output_path)  # 压缩成无密码的压缩包（为了用户下载使用）
                filepath, logShotname, extension = Utils.get_filePath_fileName_fileExt(log_path)
                print logShotname
                sourceDir_log = os.path.join(settings.uploadPath, logShotname)
                decryptZip(log_path, sourceDir_log)
                # logDir = os.path.join(sourceDir_log)  # log 解压后的路径
                configPath = os.path.join(sourceDir_log, CONFIG_FILENAME)

                remarkFile = os.path.join(sourceDir_output,"output","test_message.txt")
                if os.path.exists(remarkFile):
                    remark = open(remarkFile, 'r').read()
                else:
                    remark = ""

                config,hostName = parseConfig(configPath)
                if config is None:
                    return HttpResponse(status=400)
                else:
                    save_db(username,rDict,outputFileName + ".zip",sourceDir_log,config,hostName,remark)
                    logger.debug("入库操作成功")

        else:
            return HttpResponse(status=400)
    return HttpResponse(status=200)


def handle_uploaded_file(f, outputFile):
    '''
    存储文件
    :param f: 文件流
    :param outputFile: 输出地址
    :return:
    '''
    destination = open(outputFile, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()


def decryptZip(input, output):
    subprocess.call("unzip -P " + PASSWORD + " " + input + " -d " + output, shell=True)
    os.remove(input)


def make_zip(source_dir, output_filename):
    zipf = zipfile.ZipFile(output_filename, 'w')
    pre_len = len(os.path.dirname(source_dir))
    for parent, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            pathfile = os.path.join(parent, filename)
            arcname = pathfile[pre_len:].strip(os.path.sep)  # 相对路径
            zipf.write(pathfile, arcname)
    zipf.close()


@transaction.atomic
def parseConfig(filePath):
    try:
        json_data = open(filePath, 'r')
        json_data = json_data.read()
        configDict = json.loads(json_data)
        print configDict
        sys = taskModels.System(name=configDict['system']['name'], manufacturer=configDict['system']['manufacturer'],
                                version=configDict['system']['version'])
        sys.save()
        baseboard = taskModels.Baseboard(name=configDict['baseboard']['name'],
                                         manufacturer=configDict['baseboard']['manufacturer'],
                                         version=configDict['baseboard']['version'])
        baseboard.save()

        config = taskModels.Config(hostname=configDict['hostName'], kernel=configDict['kernel'],
                                   os=configDict['os'], board=baseboard, sys=sys)
        config.save()

        cacheInfos = configDict['cacheInfo']
        for cacheInfo in cacheInfos:
            cache = taskModels.Cache(socketdes=cacheInfo['socketdes'], size=cacheInfo['size'],
                                     operational=cacheInfo['operational'],config=config)
            cache.save()

        cpuInfos = configDict['cpuInfo']
        for cpuInfo in cpuInfos:
            cpu = taskModels.Cpu(socketdes=cpuInfo['socketdes'], manufacturer=cpuInfo['manufacturer'],
                                 version=cpuInfo['version'], maxspeed=cpuInfo['maxSpeed'],
                                 currentspeed=cpuInfo['currentSpeed'], status=cpuInfo['status'],
                                 corecount=cpuInfo['coreCount'], enabledCore=cpuInfo['coreEnabledCount'],
                                 threadcount=cpuInfo['threadCount'], config=config)
            cpu.save()

        memInfos = configDict['memInfo']
        for memInfo in memInfos:
            memory = taskModels.Memory(manufacturer=memInfo['manufacturer'], size=memInfo['size'],
                                       type=memInfo['type'], speed=memInfo['speed'],
                                       clockspeed=memInfo['clockSpeed'], banklocator=memInfo['bankLocator'],
                                       config=config)
            memory.save()

        storageInfos = configDict['storageInfo']
        for storageInfo in storageInfos:
            storage = taskModels.Storage(devicename=storageInfo['deviceName'], manufactor=storageInfo['model'],
                                        capacity=storageInfo['capacity'], sectorsize=storageInfo['sectorsize'],
                                       config=config)
            storage.save()
            partitonInfos = storageInfo['partitons']
            for partitonInfo in partitonInfos:
                partiton = taskModels.Partition(name=partitonInfo['name'], size=partitonInfo['size'],
                                     storage=storage)
                partiton.save()

        netInfos = configDict['netInfo']
        for netInfo in netInfos:
            net = taskModels.Net(interface=netInfo['interface'], bandwidth=netInfo['bankWidth'],
                                 driver=netInfo['driver'], driverversion=netInfo['driverVersion'],
                                 protocoltype=netInfo['protocolType'], address=netInfo['address'],
                                 broadcast=netInfo['broadcast'], netmask=netInfo['netmask'],
                                 network=netInfo['network'], mac=netInfo['mac'],
                                 config=config)
            net.save()
    except Exception as e:
        logger.error(str(e))
        return None
    return config,configDict['hostName']

@transaction.atomic
def parseResult(result,task):
    performance = result['results']['Performance']
    for k in performance.keys():#所有的维度值
        if not taskModels.Dimension.objects.filter(name=k).exists(): #如果不存在这样的维度值，则添加数据库
            dim = taskModels.Dimension(name = k)
            dim.save()
        else:
            dim = taskModels.Dimension.objects.get(name=k)
        dimResult = taskModels.DimResult(task=task,result=performance[k]['Total_Scores'],dim=dim)
        dimResult.save()
        parseSce(dim,k,performance,dimResult)


    # for v,k in performance.items():
    #     print v
    #     print k
@transaction.atomic
def parseTestCase(pointDict,sce,sceResult):
    '''

    :param pointDict: 场景下的  Point_Scores 的对象内容
    :param sce:  场景数据库对象
    :return:
    '''
    for k in pointDict.keys():
        datas = k.split('.')
        if len(datas) >=2:
            tool = datas[0]
            case = datas[1]
            if not taskModels.TestTool.objects.filter(name=tool).exists():
                testTool = taskModels.TestTool(name=tool)
                testTool.save()
            else:
                testTool = taskModels.TestTool.objects.get(name=tool)
            if not taskModels.TestCase.objects.filter(name=case,tool=testTool,scenario = sce).exists():
                testCase = taskModels.TestCase(tool=testTool,name=case,scenario = sce)
                testCase.save()
            else:
                testCase = taskModels.TestCase.objects.get(tool=testTool,name=case,scenario = sce)
            caseResult = taskModels.CaseResult(result=pointDict[k],case=testCase,sceResult=sceResult)
            caseResult.save()




def getCaseConfig():
    '''
    testcase 执行的命令
    :return:
    '''
    return ""


@transaction.atomic
def parseSce(dim,dimKey,performance,dimResult):
    '''
    解析维度下的所有场景，包含父子场景 （最多三级）
    :param dim: dim数据库对象
    :param dimKey: dim的key值
    :param performance: json数据对象
    :return:
    '''
    try:
        dimDict = performance[dimKey]
        for k1 in dimDict.keys():
            if k1 != 'Total_Scores': #所有的一级场景
                if not taskModels.Scenario.objects.filter(name=k1,parentid=0).exists():  # 如果不存在这样的一级场景值，则添加数据库
                    sce1 = taskModels.Scenario(name=k1,parentid=0,dim=dim)
                    sce1.save()
                else:
                    sce1 = taskModels.Scenario.objects.get(name=k1,parentid=0)
                sce1Dict = dimDict[k1]
                for k2 in sce1Dict.keys():
                    if k2 != 'Total_Scores' and k2 != 'Point_Scores': #二级场景值
                        if not taskModels.Scenario.objects.filter(name=k2, parentid=sce1.id).exists():  # 如果不存在这样的二级场景值，则添加数据库
                            sce2 = taskModels.Scenario(name=k2, parentid=sce1.id, dim=dim)
                            sce2.save()
                        else:
                            sce2 = taskModels.Scenario.objects.get(name=k2, parentid=sce1.id)
                        sce2Dict = sce1Dict[k2]
                        for k3 in sce2Dict.keys():
                            if k3 != 'Total_Scores' and k3 != 'Point_Scores':  # 二级场景值
                                if not taskModels.Scenario.objects.filter(name=k3,
                                                                          parentid=sce2.id).exists():  # 如果不存在这样的三级场景值，则添加数据库
                                    sce3 = taskModels.Scenario(name=k3, parentid=sce2.id, dim=dim)
                                    sce3.save()
                                else:
                                    sce3 = taskModels.Scenario.objects.get(name=k3, parentid=sce2.id)
                                sceResult3 = taskModels.ScenarioResult(dimresult=dimResult,scenario = sce3,
                                                                      result=dimDict[k1][k2][k3]['Total_Scores'])
                                sceResult3.save()
                                parseTestCase(dimDict[k1][k2][k3]['Point_Scores'],sce3,sceResult3)
                        sceResult2 = taskModels.ScenarioResult(dimresult=dimResult, scenario=sce2,
                                                              result=dimDict[k1][k2]['Total_Scores'])
                        sceResult2.save()
                        parseTestCase(dimDict[k1][k2]['Point_Scores'], sce2, sceResult2)
                sceResult1 = taskModels.ScenarioResult(dimresult=dimResult, scenario=sce1,
                                                       result=dimDict[k1]['Total_Scores'])
                sceResult1.save()
                parseTestCase(dimDict[k1]['Point_Scores'], sce1, sceResult1)
    except Exception as e:
        logger.error(str(e))
        return False
    return True

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
            fileName = os.path.basename(filepath)
            if filepath.endswith(".json") and fileName != CONFIG_FILENAME:
                toolName = fileName.split(".")[0]
                tools = {"toolName": toolName, "logPath": filepath}
                result_files.append(tools)
    return result_files

def parseLog(logPath,task):

    result_files = showtree(logPath)
    for tool in result_files:
        toolName = tool["toolName"]
        filePath = tool["logPath"]
        try:
            tool = taskModels.TestTool.objects.get(name = toolName)
            json_data = open(filePath, 'r')
            json_data = json_data.read()
            log = taskModels.Log(tool=tool, content=json_data, task=task)
            log.save()
        except Exception as e:
            logger.error(str(e))
            logger.error("toolName:" + toolName)




@transaction.atomic
def save_db(userName, result, outputFileName, log_path,config,hostName,remark=''):
    '''
    数据入库
    :param userName: 用户名
    :param result: 得分结果
    :param outputFileName: output 压缩包文件名
    :param log_path:    log 解压后路径
    :param config:      config文件 路径
    :param hostName:    hostName名称
    :param remark:  备注
    :return:
    '''
    try:
        owner = accountModels.UserProfile.objects.get(username=userName)
        task = taskModels.Task(owner = owner,config=config,remark=remark,delete=False,name = hostName,path = outputFileName)
        task.save()
        parseResult(result,task)
        parseLog(log_path,task)
        logger.debug("保存数据库")
    except Exception as e:
        logger.error(str(e))
        return False
    return True


def userDeal(userName):
    try:
       taskModels.UserProfile.objects.get(username=userName)
    except:
        #用户不存在
        user = taskModels.UserProfile(username=userName,name=userName)
        user.save()


# @csrf_exempt
def cert(req):
    userName = req.GET.get("userName")
    password = req.GET.get("password")
    from account.sso.authbackend import SSOAuthBackend
    result = SSOAuthBackend.authenticate_user(userName, password)
    if result:
        userDeal(userName)
        return HttpResponse("success", status=200)
    else:
        return HttpResponse("fail", status=200)


if __name__ == '__main__':
    input = "/home/qiuqiaohua/Documents/workspaces/web_workspaces/data/upload/_WS_17-12-20_10-11-26.zip"
    output = "/home/qiuqiaohua/Documents/workspaces/web_workspaces/data/upload"
    # decryptZip(input,output)

    filepath, shotname, extension = Utils.get_filePath_fileName_fileExt(input)
    print shotname
    sourceDir = os.path.join(output, shotname)
    make_zip(sourceDir, input)
