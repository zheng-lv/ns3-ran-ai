"""
这个文件定义了每个仿真活动的参数。
"""

"""
返回特定仿真活动的参数

参数:
    - campaignName: 仿真活动的名称
返回:
    - ns_path: ns-3 根目录的路径
    - ns_script: 仿真脚本的名称
    - ns_res_path: 仿真结果的路径
    - params_grid: 包含仿真参数的字典
    - figure_path: 图形文件夹的路径
"""
def get_campaign_params(campaignName):
    ns_path = './'
    ns_script = 'mmwave-gemv-integration-example'
    ns_res_path = './campaigns/' + campaignName

    if (campaignName == 'test-results'):
        numTrajectories = 50
        params_grid = {
            "RngRun": 1,
            "firstVehicleIndex": list(range(numTrajectories)),
            "numUes": 1,
            "ulIpiMicroS": 100e3,
            "dlIpiMicroS": 500e3,
            "gemvTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/bolognaLeftHalfRSU3_50vehicles_100sec/13-May-2021_'
        }
        figure_path = ns_res_path + '/figures'
    elif (campaignName == 'campaign-1'):
        numTrajectories = 50
        params_grid = {
            "RngRun": 1,
            "firstVehicleIndex": list(range(numTrajectories)),
            "numUes": 1,
            "applicationType": 'kitti',
            "kittiModel": [0, 1, 2, 1150, 1450, 1451, 1452],
            "dlIpiMicroS": 500e3,
            "gemvTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/bolognaLeftHalfRSU3_50vehicles_100sec/13-May-2021_',
            "appTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/kitti-dataset.csv'
        }
        figure_path = ns_res_path + '/figures/'
    elif (campaignName == 'test-tx-power'):
        numTrajectories = 50
        params_grid = {
            "RngRun": 1,
            "firstVehicleIndex": list(range(numTrajectories)),
            "numUes": 1,
            "applicationType": 'kitti',
            "kittiModel": [1450, 1452],
            "dlIpiMicroS": 500e3,
            "gemvTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/bolognaLeftHalfRSU3_50vehicles_100sec/13-May-2021_',
            "appTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/kitti-dataset.csv'
        }
    elif (campaignName == 'campaign-2'):
        numTrajectories = 50
        params_grid = {
            "RngRun": 1,
            "firstVehicleIndex": list(range(numTrajectories)),
            "numUes": 1,
            "applicationType": 'kitti',
            "kittiModel": [0, 1, 2, 1150, 1450, 1451, 1452],
            "txPower": 23,
            "dlIpiMicroS": 500e3,
            "gemvTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/bolognaLeftHalfRSU3_50vehicles_100sec/13-May-2021_',
            "appTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/kitti-dataset.csv'
        }
        figure_path = ns_res_path + '/figures/'
    elif (campaignName == 'test-periodicity'):
        # 采集跟踪的周期性较高的仿真
        numTrajectories = 50
        params_grid = {
            "RngRun": 1,
            "firstVehicleIndex": list(range(numTrajectories)),
            "numUes": 1,
            "applicationType": 'kitti',
            "kittiModel": [0, 1, 2, 1150, 1450, 1451, 1452],
            "txPower": 23,
            "dlIpiMicroS": 500e3,
            "gemvTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/bolognaLeftHalfRSU3_50vehicles_100sec/13-May-2021_',
            "appTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/kitti-dataset.csv',
            "tracesPeriodicity": 500
        }
        figure_path = ns_res_path + '/figures/' 
    elif (campaignName == 'offline-train-dataset'):
        ns_script = 'ran-ai'
        numTrajectories = 50
        params_grid = {
            "RngRun": 1,
            "firstVehicleIndex": list(range(numTrajectories)),
            "numUes": 2,
            "applicationType": 'kitti',
            "kittiModel": [1452],
            "dlIpiMicroS": 500e3,
            "useFakeRanAi": True,
            "simDuration": 90,
            "txPower": 23,
            "gemvTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/bolognaLeftHalfRSU3_50vehicles_100sec/13-May-2021_',
            "appTracesPath": '/media/vol2/zugnotom/rsync/ns3-mmwave-pqos/input/kitti-dataset.csv'
        }
        figure_path = ns_res_path + '/figures/'      
    else:
        print('未知的活动名称')
        exit()
    
    return (ns_path, ns_script, ns_res_path, params_grid, figure_path)
