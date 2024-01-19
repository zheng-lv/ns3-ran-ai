import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math

#check_all_infinite函数用于检查给定数据集中的所有元素是否为无穷大，如果是，则返回True，否则返回False。
def check_all_infinite(dataset):
  for el in dataset:
    if not math.isinf(el):
      return False
  return True

#plot_data函数用于绘制数据，它接受一个数据集和一个名称作为参数，并创建一个图形对象和一个坐标轴对象。然后，它遍历数据集中的选定列，并将其绘制在图形上。
def plot_data(dataset, name="rsu"):
  fig, ax = plt.subplots(figsize=(15, 15))
  #for i in range(1, len(data.columns)):
  for i in [4, 14, 25, 36]:
    if not check_all_infinite(data[i]):
      plt.plot(data[0], data[i], label="UE "+str(i))
  plt.xlabel("Time [s]")
  plt.ylabel("Received power [dBm]")
  plt.title(name)
  plt.legend()
  plt.grid(True)
  plt.savefig(name+'.png')

data = pd.read_csv("powerTest-3.txt",sep="\t", header= None)
plot_data(data, "RSU_3")

data = pd.read_csv("powerTest-4.txt",sep="\t", header= None)
plot_data(data, "RSU_4")

data = pd.read_csv("powerTest-8.txt",sep="\t", header= None)
plot_data(data, "RSU_8")

data = pd.read_csv("powerTest-10.txt",sep="\t", header= None)
plot_data(data, "RSU_10")

#最后，代码读取了一个名为losCondition-3.txt的数据文件，并使用plot_data函数绘制了所有列的数据。
#它创建了一个图形对象和一个坐标轴对象，并将所有数据绘制在同一图形上。然后，它设置了图形的标题、坐标轴标签和图例，并显示了图形。
data = pd.read_csv("losCondition-3.txt",sep="\t", header= None)
fig, ax = plt.subplots(figsize=(15, 15))
#for i in range(1, len(data.columns)):
for i in [4, 14, 25, 36]:
  plt.plot(data[0], data[i], label="UE "+str(i))
plt.xlabel("Time [s]")
plt.ylabel("Received power [dBm]")
plt.title("LOS Condition")
plt.legend()
plt.grid(True)
plt.show()
plt.savefig('LOS_3.png')
