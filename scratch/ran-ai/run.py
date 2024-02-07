from py_interface import FreeMemory, Experiment  # 导入用于Python-ns3接口的模块
from utils.Simulation import get_input, initialize_simulation  # 导入模拟设置初始化相关函数
from utils.Episode import initialize_online_episode, initialize_offline_episode, finalize_episode  # 导入剧集初始化和终止相关函数
from utils.OnlineRun import run_online_episode  # 导入在线运行相关函数
from utils.OfflineRun import run_offline_episode  # 导入离线运行相关函数
from agent.Agent import CentralizedAgent  # 导入中心化代理类
from settings.GeneralSettings import *  # 导入通用设置
from settings.StateSettings import state_dim, state_full_labels, state_normalization, state_mask  # 导入状态设置相关变量
import os  # 导入操作系统模块
import random  # 导入随机模块
import copy  # 导入拷贝模块
import argparse  # 导入命令行参数解析模块
import numpy as np  # 导入NumPy模块

parser = argparse.ArgumentParser()  # 创建命令行参数解析器

# 定义命令行参数
# 是否训练学习代理
parser.add_argument('-train', '--train', action='store_const', const=True, default=False)
# 是否测试学习代理（或其他策略）
parser.add_argument('-test', '--test', action='store_const', const=True, default=False)
# 是否执行模拟或绘制模拟结果
parser.add_argument('-run', '--run', action='store_const', const=True, default=False)
# 指定使用的策略
parser.add_argument('-policy', '--agent_policy', type=str, default='dql')
# 指定场景的KPI（远程操作或地图共享）
parser.add_argument('-mode', '--mode', type=str, default='teleoperated')
# 是否执行转移学习阶段
parser.add_argument('-transfer', '--transfer', action='store_const', const=True, default=False)
# 是否为不同的alpha值重复模拟
parser.add_argument('-multi_alpha', '--multi_alpha', action='store_const', const=True, default=False)

# 输入场景的参数
# 以下参数与代理已经训练的场景相关，默认与实际场景相同

parser.add_argument('-input_user', '--input_user_num', type=int, default=None)
parser.add_argument('-input_power', '--input_tx_power', type=int, default=None)
parser.add_argument('-input_penalty', '--input_reward_penalty', type=float, default=None)
parser.add_argument('-input_alpha', '--input_reward_alpha', type=float, default=None)
parser.add_argument('-input_episode', '--input_episode_num', type=int, default=None)
parser.add_argument('-input_step', '--input_step_num', type=int, default=None)
parser.add_argument('-input_update', '--input_update', type=str, default=None)
parser.add_argument('-input_delay', '--input_delay', type=str, default=None)
parser.add_argument('-input_offline', '--input_offline', action='store_const', const=True, default=False)

# 实际场景的参数
# 以下参数与将要训练或测试代理的场景相关

parser.add_argument('-user', '--user_num', type=int, default=1)  # 用户数量
parser.add_argument('-power', '--tx_power', type=int, default=23)  # 通信功率
parser.add_argument('-penalty', '--reward_penalty', type=float, default=10)  # 奖励函数的惩罚
parser.add_argument('-alpha', '--reward_alpha', type=float, default=1.0)  # 奖励函数的权重
parser.add_argument('-episode', '--episode_num', type=int, default=None)  # 剧集数量
parser.add_argument('-step', '--step_num', type=int, default=800)  # 步数
parser.add_argument('-update', '--update', type=str, default='real')  # 理想/真实动作更新
parser.add_argument('-delay', '--delay', type=str, default='none')  # 数据编码的额外延迟
parser.add_argument('-offline', '--offline', action='store_const', const=True, default=False)  # 是否运行离线模拟
parser.add_argument('-format', '--format', type=str, default=None)  # 输出绘图的格式

# 获取命令行参数

algorithm_training, algorithm_testing, agent_policy, running, offline_folder, transfer, \
    user_num, tx_power, reward_penalty, multi_reward_alpha, episode_num, step_num, ideal_update, additional_delay, offline_running, \
    input_user_num, input_tx_power, input_reward_penalty, input_multi_reward_alpha, input_episode_num, input_step_num, \
    input_ideal_update, input_additional_delay, input_offline_running, plot_format, mode = get_input(vars(parser.parse_args()))

# 确定通信服务的KPI

if mode == 'teleoperated':  # 如果是远程操作模式
    delay_requirement = teleoperated_delay_requirement  # 设置延迟要求
    prr_requirement = teleoperated_prr_requirement  # 设置PRR要求
    qos_bonus = 'delay'  # 设置QoS奖励为延迟
######
elif mode == 'mapsharing':  # 如果是地图共享模式
    delay_requirement = mapsharing_delay_requirement  # 设置延迟要求
    prr_requirement = mapsharing_prr_requirement  # 设置PRR要求
    qos_bonus = 'prr'  # 设置QoS奖励为PRR
else:
    raise ValueError  # 如果模式既不是远程操作也不是地图共享，则引发值错误异常

# 针对每个奖励参数reward_alpha和input_reward_alpha进行迭代
for reward_alpha, input_reward_alpha in zip(multi_reward_alpha, input_multi_reward_alpha):

    # 动作空间
    action_labels = [1450, 1451, 1452]  # 定义动作标签
    # 动作空间大小
    action_num = len(action_labels)  # 获取动作标签的数量
    # 每个动作对应的惩罚
    action_penalties = [cf_mean_per_action[action] for action in action_labels]  # 根据动作标签获取每个动作的平均惩罚
    # 最大的Chamfer距离
    max_chamfer_distance = np.max([cf_mean_per_action[action] for action in action_labels])  # 获取所有动作的平均惩罚的最大值

    # 初始化学习模型
    agent = CentralizedAgent(
        state_dim=state_dim,
        action_num=action_num,
        step_num=step_num,
        episode_num=episode_num,
        user_num=user_num,
        state_labels=state_full_labels,
        action_labels=action_labels,
        state_normalization=state_normalization,
        state_mask=state_mask,
        gamma=0.95,
        batch_size=10,
        target_replace=step_num * 10,
        memory_capacity=10000,
        learning_rate=0.00001,
        eps=0.001,
        weight_decay=0.0001,
        format=plot_format
    )

    # 初始化模拟
    data_folder, sim_duration, default_action_index, max_penalty, simulation_time, temperatures, temp = initialize_simulation(
        mode,
        algorithm_training,
        algorithm_testing,
        user_num,
        tx_power,
        reward_penalty,
        reward_alpha,
        episode_num,
        step_num,
        ideal_update,
        additional_delay,
        offline_running,
        input_user_num,
        input_tx_power,
        input_reward_penalty,
        input_reward_alpha,
        input_episode_num,
        input_step_num,
        input_ideal_update,
        input_additional_delay,
        input_offline_running,
        agent,
        transfer,
        agent_policy,
        step_duration,
        action_labels,
        action_penalties
    )


if running:  # 如果运行标志为真

    # Python-ns3接口
    if offline_running:  # 如果是离线运行模式

        ns3Settings, experiment = None, None  # 设置NS3参数和实验对象为空

    else:  # 如果是在线运行模式

        ns3Settings = {  # 设置NS3参数字典
            'numUes': user_num,  # 用户数量
            'txPower': tx_power,  # 传输功率
            'simDuration': sim_duration,  # 模拟时长
            'updatePeriodicity': step_duration,  # 更新周期
            'idealActionUpdate': ideal_update,  # 理想动作更新
            'additionalDelay': additional_delay  # 附加延迟
        }

        experiment = Experiment(mempool_key, mem_size, 'ran-ai', '../../')  # 创建实验对象

    print("Running...")  # 打印运行信息

    if offline_running:  # 如果是离线运行模式

        # 收集离线数据并将数据组织成片段
        data_folders = os.listdir(offline_folder)  # 获取离线数据文件夹列表
        vehicle_folders = []  # 车辆文件夹列表

        # 根据代理策略确定每个动作对应的轨迹片段数
        if agent_policy == 'dql':
            episode_per_action = int((episode_num + action_num) / action_num)
        else:
            episode_per_action = episode_num

        while episode_per_action > len(vehicle_folders):  # 如果片段数大于车辆文件夹数量

            random.shuffle(data_folders)  # 随机打乱数据文件夹顺序
            vehicle_folders.extend(data_folders)  # 添加数据文件夹列表到车辆文件夹列表中

        vehicle_folders = vehicle_folders[:episode_per_action]  # 取出前面片段数个车辆文件夹

        episode = -1  # 初始化片段索引

        # 遍历每个车辆轨迹
        for vehicle_folder in vehicle_folders:

            if agent_policy == 'dql':  # 如果代理策略是DQL

                shuffle_action_labels = copy.copy(action_labels)  # 复制动作标签列表
                random.shuffle(shuffle_action_labels)  # 随机打乱动作标签列表顺序

            else:  # 如果代理策略不是DQL

                shuffle_action_labels = [agent_policy]  # 设置动作标签为代理策略

            # 遍历与策略相关联的每个动作
            for action in shuffle_action_labels:

                # 开始一个新的片段
                episode += 1  # 片段索引加一

                if episode < episode_num:  # 如果片段索引小于片段数

                    episode_data = offline_folder + '/' + vehicle_folder + '/' + str(action) + '/data.pkl'  # 获取片段数据路径

                    # 初始化新片段
                    episode_start_time = initialize_offline_episode(episode,
                                                                    episode_num,
                                                                    agent,
                                                                    data_folder)

                    default_action_index = action_labels.index(int(action))  # 获取默认动作索引

                    # 运行模拟
                    run_offline_episode(user_num, state_dim, max_penalty, reward_alpha,
                                        default_action_index, action_penalties, prr_requirement,
                                        delay_requirement, algorithm_training, agent, episode_data, qos_bonus,
                                        step_num=step_num)

                    # 终止片段
                    simulation_time = finalize_episode(episode_start_time, simulation_time, episode, episode_num)

    else:  # 如果是在线运行模式

        try:  # 尝试执行以下代码

            # 遍历每个片段
            for episode in range(episode_num):

                # 初始化新片段
                temp, episode_start_time, rl, pro = initialize_online_episode(episode,
                                                                              episode_num,
                                                                              agent,
                                                                              data_folder,
                                                                              algorithm_training,
                                                                              temperatures,
                                                                              experiment,
                                                                              ns3Settings)

                # 运行模拟
                run_online_episode(action_num, user_num, state_dim, max_penalty, reward_alpha, temp, agent_policy,
                                   default_action_index, action_labels, action_penalties,
                                   prr_requirement, delay_requirement, algorithm_training, agent, rl, qos_bonus, step_num=step_num)

                # 终止片段
                simulation_time = finalize_episode(episode_start_time, simulation_time, episode, episode_num)

        finally:  # 无论是否发生异常都会执行以下代码

            experiment.kill()  # 终止实验
            del experiment  # 删除实验对象
            FreeMemory()  # 释放内存

    print("Total episode ", episode_num, "; time duration [min] ", simulation_time / 60)  # 打印总片段数和模拟时长信息

    # 保存模拟数据
    agent.save_data(data_folder)
    agent.save_model(data_folder)

    # Plot the data of the simulation

    agent.load_data(data_folder)
    agent.plot_data(data_folder, episode_num)
