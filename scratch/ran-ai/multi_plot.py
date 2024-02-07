from agent.Agent import CentralizedAgent
from plot.Boxplot import multi_boxplot
from plot.Violinplot import multi_violinplot
from plot.Histplot import multi_histplot
from settings.StateSettings import state_mask, state_dim, state_full_labels, state_labels, state_normalization
from settings.GeneralSettings import *
import numpy as np
import seaborn as sns
import os
import argparse

parser = argparse.ArgumentParser()

# Determine wheter to compare the outcomes of different simulation while varying alpha 确定是否比较不同模拟的结果，同时改变 alpha
parser.add_argument('-multi_alpha', '--multi_alpha', action='store_const', const=True, default=False)
# Determine wheter to compare the outcomes of different simulation while varying the number of users 确定是否比较不同模拟的结果，同时改变用户数量
parser.add_argument('-multi_user', '--multi_user', action='store_const', const=True, default=False)

# Parameters of the scenario analyzed 分析的场景参数
parser.add_argument('-user', '--user_num', type=int, default=1)
parser.add_argument('-policy', '--policy', type=str, default='dql')
parser.add_argument('-penalty', '--reward_penalty', type=float, default=10)
parser.add_argument('-episode', '--episode_num', type=int, default=100)
parser.add_argument('-step', '--step_num', type=int, default=800)
parser.add_argument('-power', '--power', type=int, default=23)
parser.add_argument('-alpha', '--alpha', type=float, default=1.0)
parser.add_argument('-update', '--update', type=str, default='real')
parser.add_argument('-format', '--format', type=str, default='png')
args = vars(parser.parse_args())

plot_points: int = 100
step_num: int = args['step_num']
episode_num: int = args['episode_num']
reward_penalty: float = args['reward_penalty']
state_dim: int = state_dim
plot_format: str = args['format']
action_labels: [str] = [1450, 1451, 1452]
action_num: int = len(action_labels)
state_normalization: [[]] = state_normalization

palette = sns.color_palette('rocket')

state_palette = sns.color_palette('rocket', 2)
reward_palette = sns.color_palette('rocket', 2)
qoe_palette = sns.color_palette('rocket', 3)
cd_palette = sns.color_palette('rocket_r', 3)
qos_palette = sns.color_palette('rocket', 2)

plot_state = True
plot_perf = True

test_folders: [str] = []
user_per_test: [int] = []
label_per_test: [str] = []
legend_per_test: [str] = []

label_key = None
legend_key = None

if args['multi_user'] and args['multi_alpha']:

    # 设置标签和图例的键值
    label_key = '$N_{u}$'
    legend_key = '$\\alpha$'

    # 获取策略
    policy = args['policy']

    # 定义用户数量、标签、alpha值和图例列表
    users: [int] = [1, 5]
    labels: [str] = ['1', '5']
    alphas: [float] = [0.5, 1.0]
    legends: [str] = ['0.5', '1.0']

    # 设置场景名称
    scenario_name = args['update'] + '_update/'

    # 遍历标签和用户数量
    for label, user_num in zip(labels, users):

        # 遍历图例和alpha值
        for legend, alpha in zip(legends, alphas):
            # 构建策略文件夹路径
            policy_folder = 'output/test/' + scenario_name + 'user=' + str(user_num) + '/power='\
                            + str(args['power']) + '/penalty=' + str(reward_penalty) + '/alpha='\
                            + str(alpha) + '/episode=' + str(episode_num) + '/step='\
                            + str(step_num) + '/' + policy + '/'

            # 将策略文件夹路径添加到测试文件夹列表中
            test_folders.append(policy_folder)
            # 将用户数量添加到每个测试的用户列表中
            user_per_test.append(user_num)
            # 将标签添加到每个测试的标签列表中
            label_per_test.append(label)
            # 将图例添加到每个测试的图例列表中
            legend_per_test.append(legend)

    # 设置输出文件夹路径
    output_folder = 'output/multi_test/' + scenario_name + 'multi_user/power=' + str(args['power'])\
                    + '/penalty=' + str(reward_penalty) + '/multi_alpha' + '/episode=' + str(episode_num)\
                    + '/step=' + str(step_num) + '/policy=' + args['policy'] + '/'


elif args['multi_alpha']:

    # 设置标签和图例的键值
    label_key = 'Policy'
    legend_key = '$\\alpha$'

    # 获取用户数量
    user_num: int = args['user_num']

    # 定义策略、标签、alpha值和图例列表
    policies: [str] = ['0', '1450', '1451', '1452', 'dql']
    labels: [str] = ['0', '1450', '1451', '1452', 'DQL']
    alphas: [float] = [0.5, 1.0]
    legends: [str] = ['0.5', '1.0']

    # 设置场景名称
    scenario_name = args['update'] + '_update/user=' + str(user_num) + '/power=' + str(args['power']) + \
                    '/penalty=' + str(reward_penalty)

    # 设置输出文件夹路径
    output_folder = 'output/multi_test/' + scenario_name + '/multi_alpha' + '/episode=' \
                    + str(episode_num) + '/step=' + str(step_num) + '/multi_policy/'

    # 遍历标签和策略
    for label, policy in zip(labels, policies):
        # 遍历图例和alpha值
        for legend, alpha in zip(legends, alphas):
            # 构建策略文件夹路径
            policy_folder = 'output/test/' + scenario_name + '/alpha=' + str(alpha) + '/episode=' \
                        + str(episode_num) + '/step=' + str(step_num) + '/' + policy + '/'
            # 将策略文件夹路径添加到测试文件夹列表中
            test_folders.append(policy_folder)
            # 将用户数量添加到每个测试的用户列表中
            user_per_test.append(user_num)
            # 将标签添加到每个测试的标签列表中
            label_per_test.append(label)
            # 将图例添加到每个测试的图例列表中
            legend_per_test.append(legend)


elif args['multi_user']:

    # 设置标签和图例的键值
    label_key = 'Policy'
    legend_key = '$N_{u}$'

    # 获取alpha值
    alpha = args['alpha']

    # 定义策略、标签、用户数量和图例列表
    policies: [str] = ['0', '1450', '1451', '1452', 'dql']
    labels: [str] = ['0', '1450', '1451', '1452', 'DQL']
    users: [int] = [1, 5]
    legends: [str] = ['1', '5']

    # 设置场景名称
    scenario_name = args['update'] + '_update/'

    # 遍历标签和策略
    for label, policy in zip(labels, policies):
        # 遍历图例和用户数量
        for legend, user_num in zip(legends, users):
            # 构建策略文件夹路径
            policy_folder = 'output/test/' + scenario_name + 'user=' + str(user_num) + '/power=' \
                            + str(args['power']) + '/penalty=' + str(reward_penalty) + '/alpha=' \
                            + str(alpha) + '/episode=' + str(episode_num) + '/step=' \
                            + str(step_num) + '/' + policy + '/'

            # 将策略文件夹路径添加到测试文件夹列表中
            test_folders.append(policy_folder)
            # 将用户数量添加到每个测试的用户列表中
            user_per_test.append(user_num)
            # 将标签添加到每个测试的标签列表中
            label_per_test.append(label)
            # 将图例添加到每个测试的图例列表中
            legend_per_test.append(legend)

    # 设置输出文件夹路径
    output_folder = 'output/multi_test/' + scenario_name + 'multi_user/power=' + str(args['power']) \
                    + '/penalty=' + str(reward_penalty) + '/alpha=' + str(alpha) + '/episode=' + str(episode_num) \
                    + '/step=' + str(step_num) + '/multi_policy/'

elif args['multi_policy']:

    # 设置标签键值
    label_key = 'Policy'

    # 获取用户数量
    user_num: int = args['user_num']

    # 定义策略和标签列表
    policies: [str] = ['0', '1450', '1451', '1452', 'dql']
    labels: [str] = ['0', '1450', '1451', '1452', 'DQL']

    # 设置场景名称
    scenario_name = args['update'] + '_update/user=' + str(user_num) + '/power=' + str(args['power']) + \
                    '/penalty=' + str(reward_penalty)

    # 设置输出文件夹路径
    output_folder = 'output/multi_test/' + scenario_name + '/alpha='\
                    + str(args['alpha']) + '/episode=' + str(episode_num) + '/step=' + str(step_num) + '/multi_policy/' 
                    
    # 遍历标签和策略
    for label, policy in zip(labels, policies):
        # 构建策略文件夹路径
        policy_folder = 'output/test/' + scenario_name + policy + '/'
        # 将策略文件夹路径添加到测试文件夹列表中
        test_folders.append(policy_folder)
        # 将用户数量添加到每个测试的用户列表中
        user_per_test.append(user_num)
        # 将标签添加到每个测试的标签列表中
        label_per_test.append(label)
        # 将图例添加到每个测试的图例列表中
        legend_per_test.append(None)

else:
    raise ValueError

# 遍历数据类型列表
for data_type in ['state', 'performance']:
    # 如果输出文件夹不存在，则创建
    if not os.path.exists(output_folder + data_type + '/'):
        os.makedirs(output_folder + data_type + '/')

#这段代码用于创建代理对象并加载数据。它首先计算了最大惩罚值，然后遍历每个测试文件夹，为每个文件夹创建一个中央代理对象，并将其加载到代理列表中。
test_num = len(test_folders)  # 获取测试文件夹的数量
agents = []  # 初始化代理列表
max_penalty = reward_penalty + np.max([cf_mean_per_action[action] for action in action_labels])  # 计算最大惩罚值

# 遍历每个测试文件夹 
for i, user_num in enumerate(user_per_test):
    # 创建一个中央代理对象
    agent = CentralizedAgent(
        step_num,
        episode_num,
        state_dim,
        action_num,
        user_num,
        state_full_labels,
        action_labels,
        state_normalization,
        state_mask=state_mask,
        gamma=1,
        batch_size=1,
        target_replace=1,
        memory_capacity=1,
        learning_rate=1,
        eps=1,
        weight_decay=1
    )

    # 从数据文件夹中加载数据到代理对象
    agent.load_data(test_folders[i])

    # 设置代理对象的最大惩罚值
    agent.max_penalty = max_penalty

    # 将代理对象添加到代理列表中
    agents.append(agent)

# States 这段代码用于绘制状态图。它遍历每个状态维度，对每个维度的数据进行处理，并根据需要绘制箱线图和小提琴图。

if plot_state:  # 如果需要绘制状态图

    # 遍历每个状态维度
    for i in range(state_dim):
        multi_data = []  # 多个数据
        multi_labels = []  # 多个标签
        multi_legends = []  # 多个图例
        state_key = state_labels[i]  # 获取当前状态维度的标签
        state_full_label = state_full_labels[i]  # 获取当前状态维度的完整标签
        min_value, max_value = state_normalization[i]  # 获取当前状态维度的归一化最小值和最大值

        data_idx = agents[0].data_idx  # 获取数据索引

        # 遍历每个测试文件夹
        for j in range(test_num):
            agent = agents[j]  # 获取代理对象
            label = label_per_test[j]  # 获取当前测试的标签
            legend = legend_per_test[j]  # 获取当前测试的图例

            # 计算状态数据的平均值并进行反归一化处理
            state_data = np.mean(agent.state_data, axis=0) * (max_value - min_value) + min_value

            # 将处理后的状态数据添加到多个数据列表中
            multi_data.append(state_data[i, :data_idx])

            # 添加标签和图例到对应的列表中
            multi_labels.append(label)
            multi_legends.append(legend)

        # 将多个数据列表转换为数组
        multi_data = np.stack(multi_data)

        # 绘制箱线图
        multi_boxplot(
            multi_data,
            multi_labels,
            multi_legends,
            state_key,
            label_key,
            legend_key,
            output_folder + 'state/' + state_full_label.replace(' ', '_') + '_box',  # 输出文件夹路径
            plot_format=plot_format,
            palette=state_palette
        )

        # 绘制小提琴图
        multi_violinplot(
            multi_data,
            multi_labels,
            multi_legends,
            state_key,
            label_key,
            legend_key,
            output_folder + 'state/' + state_full_label.replace(' ', '_') + '_violin',  # 输出文件夹路径
            plot_format=plot_format,
            palette=state_palette
        )

# Reward 这段代码用于绘制性能图，特别是奖励。它将每个测试的奖励数据展平后，根据需要绘制箱线图和小提琴图。

if plot_perf:  # 如果需要绘制性能图

    multi_data = []  # 多个数据
    multi_labels = []  # 多个标签
    multi_legends = []  # 多个图例

    data_idx = agents[0].data_idx  # 获取数据索引

    # 遍历每个测试文件夹
    for j in range(test_num):
        agent = agents[j]  # 获取代理对象
        label = label_per_test[j]  # 获取当前测试的标签
        legend = legend_per_test[j]  # 获取当前测试的图例

        reward_data = agent.reward_data.flatten()  # 获取奖励数据并展平

        # 将处理后的奖励数据添加到多个数据列表中
        multi_data.append(reward_data[:data_idx])
        multi_labels.append(label)
        multi_legends.append(legend)

    # 绘制箱线图
    multi_boxplot(
        multi_data,
        multi_labels,
        multi_legends,
        'Reward',  # 性能指标为奖励
        label_key,
        legend_key,
        output_folder + 'performance/reward_box',  # 输出文件夹路径
        plot_format=plot_format,
        palette=reward_palette
    )

    # 绘制小提琴图
    multi_violinplot(
        multi_data,
        multi_labels,
        multi_legends,
        'Reward',  # 性能指标为奖励
        label_key,
        legend_key,
        output_folder + 'performance/reward_violin',  # 输出文件夹路径
        plot_format=plot_format,
        palette=reward_palette
    )


# QoS (服务质量) 这段代码用于绘制服务质量（QoS）和沧菲尔距离的图表。它从每个代理对象中提取相应的数据并展平，然后根据需要绘制小提琴图和直方图

# 提取服务质量数据并展平
for j in range(test_num):
    agent = agents[j]
    label = label_per_test[j]
    legend = legend_per_test[j]

    qos_data = agent.qos_data.flatten()

    # 将处理后的服务质量数据添加到多个数据列表中
    multi_data.append(qos_data[:data_idx])
    multi_labels.append(label)
    multi_legends.append(legend)

# 绘制服务质量小提琴图
multi_violinplot(
    multi_data,
    multi_labels,
    multi_legends,
    'Quality of Service',  # 指标为服务质量
    label_key,
    legend_key,
    output_folder + 'performance/qos_violin',  # 输出文件夹路径
    plot_format=plot_format,
    palette=qos_palette
)

# 绘制服务质量直方图
multi_histplot(
    multi_data,
    multi_labels,
    multi_legends,
    'Quality of Service',  # 指标为服务质量
    label_key,
    legend_key,
    output_folder + 'performance/qos_hist',  # 输出文件夹路径
    plot_format=plot_format,
    palette=qos_palette
)

# Chamfer Distance (沧菲尔距离)

# 提取沧菲尔距离数据并展平
for j in range(test_num):
    agent = agents[j]
    label = label_per_test[j]
    legend = legend_per_test[j]

    chamfer_data = agent.chamfer_data.flatten()

    # 将处理后的沧菲尔距离数据添加到多个数据列表中
    multi_data.append(chamfer_data[:data_idx])
    multi_labels.append(label)
    multi_legends.append(legend)

# 绘制沧菲尔距离小提琴图
multi_violinplot(
    multi_data,
    multi_labels,
    multi_legends,
    'Chamfer Distance',  # 指标为沧菲尔距离
    label_key,
    legend_key,
    output_folder + 'performance/chamfer_violin',  # 输出文件夹路径
    plot_format=plot_format,
    palette=cd_palette
)

# 绘制沧菲尔距离直方图
multi_histplot(
    multi_data,
    multi_labels,
    multi_legends,
    'Chamfer Distance',  # 指标为沧菲尔距离
    label_key,
    legend_key,
    output_folder + 'performance/chamfer_hist',  # 输出文件夹路径
    plot_format=plot_format,
    palette=cd_palette
)


    # QoE (体验质量) 这段代码用于计算和绘制体验质量（QoE）的小提琴图和直方图。它从每个代理对象中提取沧菲尔距离数据，然后计算体验质量并归一化，最后根据需要绘制图表。

# 提取体验质量数据并展平
for j in range(test_num):
    agent = agents[j]
    label = label_per_test[j]
    legend = legend_per_test[j]

    # 计算体验质量，使用最大惩罚减去沧菲尔距离后再归一化
    qoe_data = (max_penalty - agent.chamfer_data.flatten()) / max_penalty

    # 将处理后的体验质量数据添加到多个数据列表中
    multi_data.append(qoe_data[:data_idx])
    multi_labels.append(label)
    multi_legends.append(legend)

# 绘制体验质量小提琴图
multi_violinplot(
    multi_data,
    multi_labels,
    multi_legends,
    'QoE',  # 指标为体验质量
    label_key,
    legend_key,
    output_folder + 'performance/qoe_violin',  # 输出文件夹路径
    plot_format=plot_format,
    palette=qoe_palette
)

# 绘制体验质量直方图
multi_histplot(
    multi_data,
    multi_labels,
    multi_legends,
    'QoE',  # 指标为体验质量
    label_key,
    legend_key,
    output_folder + 'performance/qoe_hist',  # 输出文件夹路径
    plot_format=plot_format,
    palette=qoe_palette
)
