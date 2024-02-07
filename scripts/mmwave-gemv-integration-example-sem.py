```python
from mmwave_gemv_integration_campaigns import *  # 导入模拟运行相关的自定义模块
import sem  # 导入sem库，用于管理模拟运行
import numpy as np  # 导入NumPy库，用于数值计算
import pandas as pd  # 导入Pandas库，用于数据处理
import matplotlib.pyplot as plt  # 导入Matplotlib库，用于绘图
# # Temporarily limit number of max cores used
# sem.parallelrunner.MAX_PARALLEL_PROCESSES = 1  # 临时限制最大使用核心数

campaignName  = 'offline-train-dataset'  # 设置模拟运行的名称
(ns_path, ns_script, ns_res_path, 
 params_grid, _) = get_campaign_params (campaignName)  # 调用get_campaign_params()函数获取模拟运行的参数信息

# 创建一个新的模拟运行实例，并指定模拟运行的路径、脚本以及结果存储的路径等参数
campaign = sem.CampaignManager.new (ns_path=ns_path, script=ns_script, campaign_dir=ns_res_path, 
                                    optimized=True, check_repo=False, overwrite=False)
    
overall_list = sem.list_param_combinations(params_grid)  # 获取所有参数组合

print ("Run simulations")  # 打印提示信息，表示开始运行模拟
# 运行缺失的模拟实例，以确保所有参数组合都已经运行
campaign.run_missing_simulations(overall_list)

def check_errors(result):
    # 获取模拟结果的错误文件名
    result_filenames = campaign.db.get_result_files(result['meta']['id'])
    result_filename = result_filenames['stderr']
    with open(result_filename, 'r') as result_file:
        error_file = result_file.read()  # 读取错误文件内容
        # 检查错误文件内容，如果不为空则返回1，表示有错误发生，否则返回0
        if (len(error_file) != 0):
            return 1
        else:
            return 0

results = campaign.db.get_results()  # 获取所有模拟结果

# 统计模拟结果中发生的错误数量
errors = []
for result_entry in results:
    errors.append(check_errors(result_entry))

num_errors = sum(errors)  # 计算错误数量总和
# 打印错误信息统计结果
print(f'Overall, we have {num_errors} errors out of {len(results)} simulations!')
```
