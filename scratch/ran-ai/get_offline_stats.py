import sem  # 导入 sem 模块
import pandas as pd  # 导入 pandas 库并重命名为 pd
import os  # 导入 os 模块
import sys  # 导入 sys 模块
import argparse  # 导入 argparse 模块

# 将脚本所在目录添加到 sys.path 中
sys.path.insert(1, '../../')

# 导入自定义模块 mmwavePlotUtils 中的 read_ran_ai 函数
from scripts.mmwavePlotUtils import read_ran_ai

# 创建参数解析器
parser = argparse.ArgumentParser()

# 添加命令行参数
parser.add_argument('-run', '--run', action='store_const', const=True, default=False)  # 是否运行仿真
parser.add_argument('-user', '--user_num', type=int, default=1)  # 用户数量
parser.add_argument('-power', '--tx_power', type=int, default=23)  # 通信功率
parser.add_argument('-rep', '--repetition', type=int, default=1)  # 重复次数
parser.add_argument('-sim_duration', '--sim_duration', type=int, default=85)  # 仿真持续时间
parser.add_argument('-ideal_update', '--ideal_update', action='store_const', const=True, default=False)  # 理想更新或真实更新
parser.add_argument('-add_delay', '--add_delay', action='store_const', const=True, default=False)  # 是否考虑额外延迟

# 解析命令行参数并将其转换为字典形式
args = vars(parser.parse_args())

# 设置 pandas 显示选项
pd.set_option("display.max_rows", 100000, "display.max_columns", 100000)

# 定义一些参数和常量
campaign_name = 'trial'  # 试验名称
rng_range = list(range(1, args['repetition'] + 1))  # 重复次数范围
vehicle_index_range = list(range(1, 51))  # 车辆索引范围
application_range = [1450, 1451, 1452]  # 应用程序压缩模型范围
user_num = args['user_num']  # 用户数量
tx_power = args['tx_power']  # 通信功率
sim_duration = args['sim_duration']  # 仿真持续时间
ideal_update = args['ideal_update']  # 是否理想更新
add_delay = args['add_delay']  # 是否考虑额外延迟

# 定义参数网格
params_grid = {
    "RngRun": rng_range,
    "firstVehicleIndex": vehicle_index_range,
    "numUes": user_num,
    "applicationType": 'kitti',
    "kittiModel": application_range,
    "useFakeRanAi": True,
    "simDuration": sim_duration,
    "txPower": tx_power,
    "idealActionUpdate": ideal_update,
    "additionalDelay": add_delay,
    "gemvTracesPath": '/home/masonfed/git_repos/ns3-mmwave-pqos/input/bolognaLeftHalfRSU3_50vehicles_100sec/13-May-2021_',
    "appTracesPath": '/home/masonfed/git_repos/ns3-mmwave-pqos/input/kitti-dataset.csv',
}

# 生成原始数据和处理后数据存储路径
raw_path = 'offline_dataset/'
process_path = 'offline_dataset/'

if ideal_update:
    if add_delay:
        raw_path += 'ideal_update_add_delay/user=' + str(user_num) + '/power=' + str(tx_power) + '/raw_data/'
        process_path += 'ideal_update_add_delay/user=' + str(user_num) + '/power=' + str(tx_power) + '/process_data/'
    else:
        raw_path += 'ideal_update/user=' + str(user_num) + '/power=' + str(tx_power) + '/raw_data/'
        process_path += 'ideal_update/user=' + str(user_num) + '/power=' + str(tx_power) + '/process_data/'
else:
    if add_delay:
        raw_path += 'real_update_add_delay/user=' + str(user_num) + '/power=' + str(tx_power) + '/raw_data/'
        process_path += 'real_update_add_delay/user=' + str(user_num) + '/power=' + str(tx_power) + '/process_data/'
    else:
        raw_path += 'real_update/user=' + str(user_num) + '/

///
# 检查原始数据存储路径是否存在，如果不存在则创建
if not os.path.exists(raw_path):
    os.makedirs(raw_path)

# 检查处理后数据存储路径是否存在，如果不存在则创建
if not os.path.exists(process_path):
    os.makedirs(process_path)

# 运行 ns3 仿真

# 设置 ns3 执行路径
ns_path = '../../'
# 指定 ns3 脚本
ns_script = 'ran-ai'

# 创建一个新的仿真管理器实例
campaign = sem.CampaignManager.new(ns_path=ns_path, script=ns_script, campaign_dir=raw_path, check_repo=False,
                                   overwrite=True, runner_type="ParallelRunner")

# 生成参数组合列表
overall_list = sem.list_param_combinations(params_grid)

# 如果命令行参数中包含 '-run'，则运行缺失的仿真
if args['run']:
    campaign.run_missing_simulations(overall_list)

# 获取仿真结果
results = campaign.db.get_results()

# 处理 ns3 仿真数据

# 初始化运行编号
run = -1

# 遍历重复次数范围
for rng in rng_range:
    # 遍历车辆索引范围
    for vehicleIndex in vehicle_index_range:
        # 更新运行编号
        run += 1
        # 遍历应用程序压缩模型范围
        for kittiModel in application_range:
            # 更新参数网格中的车辆索引和应用程序模型
            params_grid["firstVehicleIndex"] = vehicleIndex
            params_grid["kittiModel"] = kittiModel

            # 重新生成参数组合列表
            overall_list = sem.list_param_combinations(params_grid)

            # 从仿真管理器中获取结果并将其作为 DataFrame 返回
            results = campaign.get_results_as_dataframe(read_ran_ai,
                                                        params=overall_list,
                                                        verbose=True,
                                                        parallel_parsing=False)

            # 构建新输出路径
            new_outputs_path = process_path + str(run) + '/' + str(kittiModel) + '/'

            # 如果新输出路径不存在，则创建
            if not os.path.exists(new_outputs_path):
                os.makedirs(new_outputs_path)

            # 将结果保存为 pickle 文件
            results.to_pickle(new_outputs_path + 'data.pkl')
