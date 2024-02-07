```python
import pandas as pd  # 导入 pandas 库，用于数据处理
from math import ceil  # 导入 ceil 函数，用于向上取整
import matplotlib.pyplot as plt  # 导入 matplotlib 库，用于绘图
from matplotlib.backends.backend_pdf import PdfPages  # 导入 PdfPages 类，用于将图保存为 PDF 格式
import matplotlib.colors as colors  # 导入 matplotlib.colors 模块，用于处理颜色
import numpy as np  # 导入 numpy 库，用于数值计算

"""
This files contains some utilities functions
"""  # 文件包含一些实用函数

"""
Save figure in pdf format

Params: 
    - fig: the pyplot figure
    - path: the figure path
"""  # 将图保存为 PDF 格式的函数
def save_figure(fig, path):
    overwrite = True  # 是否覆盖已存在的文件
    plt.figure(fig.number)  # 获取指定编号的图
    if overwrite == False and Path(path).exists():  # 如果不覆盖且文件已存在
        input("File already exists, overwrite?")  # 提示用户是否覆盖文件
    pdf = PdfPages(path)  # 创建 PdfPages 对象
    pdf.savefig()  # 将图保存到 PDF
    pdf.close()  # 关闭 PDF 文件
    plt.close()  # 关闭图

"""
Produce a figure with multiple subplots of a given metric. Each subplot 
corresponds to a different firstVehicleIndex  

Params: 
    - results: dataframe containing the simulation results
    - xMetric: the metric on the x axis
    - yMetric: the metric on the y axis
    - figName: the name of the figure
    - style: the style of the plot
"""  # 绘制多个子图的函数，每个子图对应不同的 firstVehicleIndex
def plot_stat(results, xMetric, yMetric, figName, style='-'):
    num_cols = 5  # 每行的子图数量
    num_plots = len(results['firstVehicleIndex'].unique())  # 总共的子图数量
    num_rows = ceil(num_plots / num_cols)  # 计算行数
    fig, ax = plt.subplots(num_rows, num_cols, figsize=(7*num_rows, 9*num_cols), 
                            squeeze=False)  # 创建子图
    
    for i in results['firstVehicleIndex'].unique():
        x = results[(results['firstVehicleIndex'] == i)][xMetric]  # 获取 x 数据
        y = results[(results['firstVehicleIndex'] == i)][yMetric]  # 获取 y 数据
        row_index = int(i / num_cols)  # 行索引
        col_index = i % num_cols  # 列索引
        ax[row_index, col_index].plot(x, y, style)  # 绘制子图
        ax[row_index, col_index].grid()  # 显示网格
        ax[row_index, col_index].set_title('Vehicle ' + str(i))  # 设置标题
        ax[row_index, col_index].set_xlabel(xMetric)  # 设置 x 轴标签
        ax[row_index, col_index].set_ylabel(yMetric)  # 设置 y 轴标签
        if (yMetric == 'avg prr' or yMetric == 'avg throughput [bps]' or yMetric == 'delay [s]'):
            ax[row_index, col_index].set_ylim(bottom=0, top=max(y)*1.1)  # 设置 y 轴范围
    fig.tight_layout()  # 调整布局
    save_figure(fig, figName + '.pdf')  # 保存图

"""
Associates a metric measured by a certain vehicle over multiple time instants 
with the visited positions  

Params: 
    - vehicleIndex: the index of the vehicle to consider
    - rlcOrPdcpStat: dataframe containing the simulation results (works only 
                     with RLC, PDCP or APP results)
    - metric: the metric to consider
Return:
    - x: list of x coordinates visited by the vehicle
    - y: list of y coordinates visited by the vehicle
    - z: list of values measured at each location 
"""  # 将某辆车测得的指标与其访问的位置关联起来的函数
def map_position_to_metric_single_vehicle(vehicleIndex, rlcOrPdcpStat, metric):
    mobilityPath = "input/bolognaLeftHalfRSU3_50vehicles_100sec/mobility/nodes/"
    mobilityDf = pd.read_csv(mobilityPath + "node-" + str(vehicleIndex) + ".txt", 
                              header=None, delimiter=" ", names=['time [s]', 'x', 'y']) 
    rlcOrPdcpStat = rlcOrPdcpStat[(rlcOrPdcpStat['firstVehicleIndex'] == vehicleIndex)][['start [s]','end [s]', metric]]
    x = []
    y = []
    z = []
    for index, row in mobilityDf.iterrows():
        values = rlcOrPdcpStat[(row['time [s]'] >= rlcOrPdcpStat['start [s]']) &
                                (row['time [s]'] < rlcOrPdcpStat['end [s]'])][metric].values
        if (len(values) == 0):
            continue
        if (len(values) > 1):
            print(rlcOrPdcpStat[(row['time [s]'] >= rlcOrPdcpStat['start [s]']) &
                                    (row['time [s]'] < rlcOrPdcpStat['end [s]'])])
            print("Error: more than 1 delay value")
            exit()
        x += [float(row['x'])]
        y += [float(row['y'])]
        z += [float(values[0])]
    return x, y, z

"""
Associates a metric measured by multiple vehicles over multiple time instants 
with the visited positions.   

Params: 
    - rlcOrPdcpStat: dataframe containing the simulation results (works only 
                     with RLC, PDCP or APP results)
    - metric: the metric to consider
Return:
    - x: list of x coordinates visited by the vehicle
    - y: list of y coordinates visited by the vehicle
    - z: list of average values measured at each location 
"""  # 将多辆车测得的指标与其访问的位置关联起来的函数
def map_position_to_metric(rlcOrPdcpResult, metric):
    allXYZ = pd.DataFrame()
    for i in rlcOrPdcpResult['firstVehicleIndex'].unique():
        (x, y, z) = map_position_to_metric_single_vehicle(i

, rlcOrPdcpResult, metric)
        data = {'x': x, 'y': y, metric: z}
        allXYZ = allXYZ.append(pd.DataFrame(data), ignore_index=True)
    return allXYZ   
         
"""
Produces a map plot in which each point represents a visited location. 
The color of each point indicates the value of a certain metric measured in 
that location. 
If for a certain location there are multiple measurements (e.g., in case 
different vehicles visit the same location), the value corresponds to the average 
of all the measurements.  

Params: 
    - rlcOrPdcpResult: dataframe containing the simulation results (works only 
                       with RLC, PDCP or APP results)
    - metric: the metric to consider
    - figName: the name of the figure (full path)
    - gamma: parameter to adjust the color bar 
"""  # 在地图上绘制测量指标的函数
def plot_metric_map(rlcOrPdcpResult, metric, figName, gamma=0.5):
    fig, ax = plt.subplots(1, 1)
    ax.grid()
    allXYZ = map_position_to_metric(rlcOrPdcpStat, metric)
    
    # if multiple measures are available for the same position, compute the
    # average
    allXYZ = allXYZ.groupby(['x', 'y'], as_index=False).mean()
    vMax = max(allXYZ[metric])
    if (metric == 'avg prr'):
        vMax = 1
    im = ax.scatter(allXYZ['x'], allXYZ['y'], c=allXYZ[metric], s=0.7,
                     norm=colors.PowerNorm(gamma=gamma), cmap="rainbow", 
                     vmin=0, vmax=vMax)
    ax.set_xlim([11.310, 11.3215])
    ax.set_ylim([44.491, 44.4975])
    ax.ticklabel_format(useOffset=False)
    fig.colorbar(im, ax=ax)
    plt.title(metric)
    save_figure(fig, figName + '.pdf')

"""
Produces a box plot for a certain metric.  

Params: 
    - rlcOrPdcpResult: dataframe containing the simulation results (works only 
                       with RLC, PDCP or APP results)
    - metric: the metric to consider
    - figName: the name of the figure (full path)
"""  # 绘制箱线图的函数
def plot_box(rlcOrPdcpResult, metric, figName):
    fig, ax = plt.subplots(1, 1)
    ax.grid()
    ax.violinplot(rlcOrPdcpResult[metric], showmeans=True)
    ax.set_ylabel(metric)
    save_figure(fig, figName + '.pdf')
```
