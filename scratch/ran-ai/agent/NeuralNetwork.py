from abc import ABC  # 导入ABC（Abstract Base Class）抽象基类
import torch  # 导入PyTorch库
from torch.nn import Module  # 从torch.nn模块导入Module类


class LinearNeuralNetwork(Module, ABC):
    """
    LinearNeuralNetwork类
    定义了一个基本的线性神经网络，用于估计动作的Q值
    """

    def __init__(self,
                 input_dim: int,  # 输入维度
                 output_dim: int  # 输出维度
                 ):

        super(LinearNeuralNetwork, self).__init__()  # 调用父类Module的初始化方法

        # 线性层
        self.linear_1 = torch.nn.Linear(input_dim, 12)  # 第一个线性层，输入维度为input_dim，输出维度为12
        self.linear_2 = torch.nn.Linear(12, 6)  # 第二个线性层，输入维度为12，输出维度为6
        self.linear_3 = torch.nn.Linear(6, output_dim)  # 第三个线性层，输入维度为6，输出维度为output_dim

        # 初始化每一层的权重
        torch.nn.init.kaiming_uniform_(self.linear_1.weight, nonlinearity='relu')  # 使用kaiming_uniform_初始化第一层的权重
        torch.nn.init.kaiming_uniform_(self.linear_2.weight, nonlinearity='relu')  # 使用kaiming_uniform_初始化第二层的权重
        torch.nn.init.uniform_(self.linear_3.weight)  # 使用uniform_初始化第三层的权重

        # 初始化每一层的偏置
        torch.nn.init.zeros_(self.linear_1.bias)  # 初始化第一层的偏置为零
        torch.nn.init.zeros_(self.linear_2.bias)  # 初始化第二层的偏置为零
        torch.nn.init.uniform_(self.linear_3.bias)  # 使用uniform_初始化第三层的偏置

    def forward(self, x: torch.Tensor):
        """
        forward方法
        计算输入张量x的Q值
        """

        x = torch.nn.functional.relu(self.linear_1(x))  # 使用ReLU激活函数计算第一层的输出
        x = torch.nn.functional.relu(self.linear_2(x))  # 使用ReLU激活函数计算第二层的输出
        x = self.linear_3(x)  # 计算第三层的输出

        return x  # 返回输出张量x
