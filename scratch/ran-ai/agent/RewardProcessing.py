import numpy as np

# 定义奖励处理函数
def reward_process(step_data_per_user,
                   prr_features: [],
                   app_delay_label: str,
                   app_prr_requirement: float,
                   app_delay_requirement: float,
                   last_actions: [int],
                   cd_per_action: [float],
                   user_num: int,
                   max_penalty: float,
                   reward_alpha: float,
                   online: bool,
                   qos_bonus: str):
    """
    对每个用户的奖励进行处理

    Parameters:
        step_data_per_user (list): 每个用户的步骤数据列表
        prr_features (list): PRR 特征列表
        app_delay_label (str): 应用延迟标签
        app_prr_requirement (float): 应用 PRR 要求
        app_delay_requirement (float): 应用延迟要求
        last_actions (list): 上次动作列表
        cd_per_action (list): 每个动作的 CD（Chamfer Distance）
        user_num (int): 用户数量
        max_penalty (float): 最大惩罚
        reward_alpha (float): 奖励系数
        online (bool): 是否在线
        qos_bonus (str): QoS 奖励类型

    Returns:
        rewards (np.ndarray): 每个用户的奖励数组
        qos_per_user (list): 每个用户的 QoS
        cd_per_user (list): 每个用户的 CD
    """

    qos_per_user = [None] * user_num  # 初始化每个用户的 QoS
    cd_per_user = [None] * user_num  # 初始化每个用户的 CD
    rewards = [None] * user_num  # 初始化每个用户的奖励

    imsi_list = []  # IMSI 列表

    # 遍历每个用户的场景
    for user_idx in range(user_num):

        step_data = step_data_per_user[user_idx]  # 获取当前用户的步骤数据

        if online:
            imsi_list.append(int(step_data[0]))  # 在线时添加 IMSI
        else:
            imsi_list.append(step_data['IMSI'])  # 离线时添加 IMSI

        # 计算 PRR
        num, den = step_data[prr_features[0][0]], step_data[prr_features[0][1]]
        if den == 0:
            prr = 1
        else:
            prr = num / den
        
        delay = step_data[app_delay_label]  # 获取应用延迟
        cd_per_user[user_idx] = cd_per_action[last_actions[user_idx]]  # 获取用户的 CD

        # 如果满足通信 KPI 要求
        if delay < app_delay_requirement and prr >= app_prr_requirement:

            # 如果满足通信 KPI 要求，计算 QoS
            qos_per_user[user_idx] = 1
            cd_penalty = cd_per_user[user_idx] / max_penalty

            if qos_bonus == 'delay':
                qos_penalty = delay / app_delay_requirement
            elif qos_bonus == 'prr':
                qos_penalty = app_prr_requirement / prr
            else:
                raise ValueError

        else:
            # 如果未满足通信 KPI 要求
            qos_per_user[user_idx] = 0
            cd_penalty = 1
            qos_penalty = 1

        # 分配奖励给用户
        rewards[user_idx] = 1 - reward_alpha * cd_penalty - (1 - reward_alpha) * qos_penalty

    rewards = np.asarray(rewards, dtype=float)  # 转换为 NumPy 数组

    # 将奖励归一化到 [-1, +1]
    rewards -= 0.5
    rewards *= 2

    return rewards, qos_per_user, cd_per_user


# 获取每个动作的奖励
def get_reward_per_action(penalty_per_action: [float], reward_penalty: float):
    """
    获取每个动作的奖励

    Parameters:
        penalty_per_action (list): 每个动作的惩罚列表
        reward_penalty (float): 奖励惩罚

    Returns:
        reward_per_action (np.ndarray): 每个动作的奖励数组
    """

    reward_penalty += np.max(penalty_per_action)  # 奖励惩罚

    # 计算每个动作的奖励
    reward_per_action = np.array([reward_penalty / 2 - penalty for penalty in penalty_per_action]) / (
            reward_penalty / 2)

    return reward_per_action
