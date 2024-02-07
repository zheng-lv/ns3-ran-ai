import numpy as np

def state_process(step_data_per_user,
                  features: [],
                  feature_normalization: [],
                  combination_features: [],
                  combination_feature_normalization: [],
                  state_dim: int,
                  user_num: int,
                  online: bool):
    """
    对状态进行处理的函数。

    参数:
        step_data_per_user (list): 包含每个用户数据的列表。
        features (list): 单独特征的标签列表。
        feature_normalization (list): 单独特征的归一化范围列表。
        combination_features (list): 组合特征的标签列表。
        combination_feature_normalization (list): 组合特征的归一化范围列表。
        state_dim (int): 状态的维度。
        user_num (int): 用户数量。
        online (bool): 是否在线数据。

    返回:
        states (list): 处理后的状态列表。
        imsi_list (list): 用户IMSI列表。
    """
    states = [np.zeros(state_dim) for _ in range(user_num)]  # 初始化状态列表

    feature_num = len(features)  # 获取单独特征的数量

    imsi_list = []  # 初始化用户IMSI列表

    # 遍历每个用户的数据
    for user_idx in range(user_num):

        step_data = step_data_per_user[user_idx]  # 获取当前用户的数据

        if online:
            imsi_list.append(int(step_data[0]))  # 如果是在线数据，从数据中获取IMSI
        else:
            imsi_list.append(step_data['IMSI'])  # 如果不是在线数据，从数据中获取IMSI

        # 添加单独特征到状态中
        for state_idx, label in enumerate(features):

            feature = step_data[label]  # 获取单独特征的值

            min_value = feature_normalization[state_idx][0]  # 获取归一化的最小值
            max_value = feature_normalization[state_idx][1]  # 获取归一化的最大值

            feature = np.max((min_value, feature))  # 取特征值和最小值中的较大值
            feature = np.min((max_value, feature))  # 取特征值和最大值中的较小值
            feature = (feature - min_value) / (max_value - min_value)  # 归一化特征值

            states[user_idx][state_idx] = feature  # 将归一化后的特征值添加到状态列表中

        # 添加PRR值到状态中
        for state_idx, comb_features in enumerate(combination_features):

            num, den = step_data[comb_features[0]], step_data[comb_features[1]]  # 获取PRR的分子和分母

            min_value = combination_feature_normalization[state_idx][0]  # 获取组合特征的归一化最小值
            max_value = combination_feature_normalization[state_idx][1]  # 获取组合特征的归一化最大值

            if den <= 0:
                feature = 1  # 如果分母小于等于0，则将特征值设为1
            else:
                feature = num / den  # 计算PRR值

            feature = np.max((min_value, feature))  # 取特征值和最小值中的较大值
            feature = np.min((max_value, feature))  # 取特征值和最大值中的较小值
            feature = (feature - min_value) / (max_value - min_value)  # 归一化特征值

            states[user_idx][state_idx + feature_num] = feature  # 将归一化后的特征值添加到状态列表中

    return states, imsi_list  # 返回处理后的状态列表和IMSI列表
