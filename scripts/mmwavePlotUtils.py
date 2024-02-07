import sem  # 导入 sem 模块
import pandas as pd  # 导入 pandas 库并将其别名为 pd
from io import StringIO  # 从 io 模块导入 StringIO
import matplotlib.pyplot as plt  # 导入 matplotlib.pyplot 模块并将其别名为 plt

"""
    读取 RxPacketTrace.txt 跟踪文件并返回包含解析值的列表。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    参数:
        result (str): RxPacketTrace.txt 的内容，类型为字符串
"""
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(['UL/DL', 'Time [s]', 'OFDM symbols', 'Cell ID', 'RNTI', 
                          'CC ID', 'TB size [bytes]', 'MCS', 'SINR [dB]'])  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*RxPacketTrace.txt')  # 指定只加载某些文件
def read_rxPacketTrace(result):    
    data = []  # 初始化一个空列表以存储解析的值
    lines = result['output']['RxPacketTrace.txt'].splitlines()  # 将 RxPacketTrace.txt 的内容按行拆分
    for line in lines[1:]:  # 遍历每一行，跳过标题行
        values = line.split("\t")  # 使用制表符分割每一行
        row = [values[0],  # 模式 (UL/DL)
               float(values[1]),  # 时间 [s]
               int(values[6]),  # OFDM 符号
               int(values[7]),  # 小区 ID
               int(values[8]),  # RNTI
               int(values[9]),  # CC ID
               int(values[10]),  # TB 大小 [字节]
               int(values[11]),  # MCS
               float(values[13])]  # SINR [dB]
        data += [row]  # 将解析的值附加到 data 列表
    return data  # 返回包含解析值的列表

# 解析和提取 PDCP 和 RLC 统计信息的函数
def read_pdcpAndRlcStats(values):
    start = float(values[0])  # 起始时间
    end = float(values[1])  # 结束时间
    numTxPdus = int(values[6])  # 发送的 PDU 数量
    txBytes = int(values[7])  # 发送的字节数
    numRxPdus = int(values[8])  # 接收的 PDU 数量
    rxBytes = int(values[9])  # 接收的字节数
    
    # 创建包含解析值的行
    row = [start, end, int(values[2]), int(values[3]), int(values[4]), int(values[5]), numTxPdus,
           txBytes, int(values[8]), rxBytes, float(values[10]), float(values[11]), float(values[12]),
           float(values[13]), txBytes * 8 / (end - start), rxBytes * 8 / (end - start),
           numRxPdus / numTxPdus]
    return row  # 返回行

# PDCP 和 RLC 统计信息的标签列表
pdcpAndRlcLabels = ['start [s]', 'end [s]', 'Cell ID', 'IMSI', 'RNTI', 'LCID', 'num tx PDUs', 'tx bytes',
                    'num rx PDUs', 'rx bytes', 'delay [s]', 'delay std dev', 'delay min', 'delay max',
                    'avg goodput [bps]', 'avg throughput [bps]', 'avg prr']

"""
    读取 DlPdcpStats.txt 跟踪文件并返回包含解析值的列表。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    注意: 仅当跟踪文件包含聚合统计信息时，此函数才有效。请确保属性 ns3::MmWaveBearerStatsCalculator::AggregatedStats 设置为 True
    参数:
        result (str): DlPdcpStats.txt 的内容，类型为字符串
"""    
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(pdcpAndRlcLabels)  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*DlPdcpStats.txt')  # 指定只加载某些文件
def read_dlPdcpStatsTrace(result):    
    data = []  # 初始化一个空列表以存储解析的值
    lines = result['output']['DlPdcpStats.txt'].splitlines()  # 将 DlPdcpStats.txt 的内容按行拆分
    for line in lines[1:]:  # 遍历每一行
        values = line.split("\t")  # 使用制表符分割每一行
        row = read_pdcpAndRlcStats(values)  # 调用函数解析 PDCP 和 RLC 统计信息
        data += [row]  # 将解析的值附加到 data 列表
    return data  # 返回包含解析值的列表

"""
    读取 UlPdcpStats.txt 跟踪文件并返回包含解析值的列表。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    注意: 仅当跟踪文件包含聚合统计信息时，此函数才有效。请确保属性 ns3::MmWaveBearerStatsCalculator::AggregatedStats 设置为 True
    参数:
        result (str): UlPdcpStats.txt 的内容，类型为字符串
"""    
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(pdcpAndRlcLabels)  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*UlPdcpStats.txt')  # 指定只加载某些文件
def read_ulPdcpStatsTrace(result):    
    data = []  # 初始化一个空列表以存储解析的值
    lines = result['output']['UlPdcpStats.txt'].splitlines()  # 将 UlPdcpStats.txt 的内容按行拆分
    for line in lines[1:]:  # 遍历每一行
        values = line.split("\t")  # 使用制表符分割每一行
        row = read_pdcpAndRlcStats(values)  # 调用函数解析 PDCP 和 RLC 统计信息
        data += [row]  # 将解析的值附加到 data 列表
    return data  # 返回包含解析值的列表

"""
    读取 DlRlcStats.txt 跟踪文件并返回包含解析值的列表。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    注意: 仅当跟踪文件包含聚合统计信息时，此函数才有效。请确保属性 ns3::MmWaveBearerStatsCalculator::AggregatedStats 设置为 True
    参数:
        result (str): DlRlcStats.txt 的内容，类型为字符串
"""    
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(pdcpAndRlcLabels)  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*DlRlcStats.txt')  # 指定只加载某些文件
def read_dlRlcStatsTrace(result):    
    data = []  # 初始化一个空列表以存储解析的值
    lines = result['output']['DlRlcStats.txt'].splitlines()  # 将 DlRlcStats.txt 的内容按行拆分
    for line in lines[1:]:  # 遍历每一行
        values = line.split("\t")  # 使用制表符分割每一行
        row = read_pdcpAndRlcStats(values)  # 调用函数解析 PDCP 和 RLC 统计信息
        data += [row]  # 将解析的值附加到 data 列表
    return data  # 返回包含解析值的列表

"""
    读取 UlRlcStats.txt 跟踪文件并返回包含解析值的列表。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    注意: 仅当跟踪文件包含聚合统计信息时，此函数才有效。请确保属性 ns3::MmWaveBearerStatsCalculator::AggregatedStats 设置为 True
    参数:
        result (str): UlRlcStats.txt 的内容，类型为字符串
"""    
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(pdcpAndRlcLabels)  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*UlRlcStats.txt')  # 指定只加载某些文件
def read_ulRlcStatsTrace(result):    
    data = []  # 初始化一个空列表以存储解析的值
    lines = result['output']['UlRlcStats.txt'].splitlines()  # 将 UlRlcStats.txt 的内容按行拆分
    for line in lines[1:]:  # 遍历每一行
        values = line.split("\t")  # 使用制表符分割每一行
        row = read_pdcpAndRlcStats(values)  # 调用函数解析 PDCP 和 RLC 统计信息
        data += [row]  # 将解析的值附加到 data 列表
    return data  # 返回包含解析值的列表
    
"""
    读取 AppStats.txt 跟踪文件并返回包含解析值的列表。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    参数:
        result (str): AppStats.txt 的内容，类型为字符串
"""
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(['start [s]', 'end [s]', 'NodeId', 'nTxBursts', 'TxBytes', 
                          'nRxBursts', 'RxBytes', 'delay [s]', 'stdDev', 'min', 
                          'max', 'avg prr', 'avg throughput [bps]'])  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*AppStats.txt')  # 指定只加载某些文件
def read_appStatsTrace(result):    
    data = []  # 初始化一个空列表以存储解析的值
    lines = result['output']['AppStats.txt'].splitlines()  # 将 AppStats.txt 的内容按行拆分
    for line in lines[1:]:  # 遍历每一行
        values = line.split("\t")  # 使用制表符分割每一行
        start = float(values[0])  # 起始时间
        end = float(values[1])  # 结束时间
        nTxBursts = int(values[3])  # 发送的突发数量
        nRxBursts = int(values[5])  # 接收的突发数量
        rxBytes = int(values[6])  # 接收的字节数
        row = [start, end, int(values[2]), nTxBursts, int(values[4]), nRxBursts, rxBytes,
               float(values[7]) / 1e9, float(values[8]), float(values[9]), float(values[10]),
               nRxBursts / nTxBursts, rxBytes * 8 / (end - start)]  # 创建包含解析值的行
        data += [row]  # 将解析的值附加到 data 列表
    return data  # 返回包含解析值的列表

    
"""
    读取 RxPacketTrace.txt 跟踪文件，使用采样时间 100 毫秒解析它，并返回包含采样值的列表。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    参数:
        result (str): RxPacketTrace.txt 的内容，类型为字符串
"""
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(['Time [s]', 'OFDM symbols', 'Cell ID', 'RNTI', 
                          'CC ID', 'TB size [bytes]', 'MCS', 'SINR [dB]', 'UL/DL'])  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*RxPacketTrace.txt')  # 指定只加载某些文件
def sample_rxPacketTrace(result):    
    data = []  # 初始化一个空列表以存储解析的值
    df = pd.read_csv(StringIO(result['output']['RxPacketTrace.txt']), 
                     delimiter="\t", index_col=False, 
                     usecols=[0, 1, 6, 7, 8, 9, 10, 11, 13], 
                     names=['UL/DL', 'Time [s]', 'OFDM symbols', 'Cell ID', 
                            'RNTI', 'CC ID', 'TB size [bytes]', 'MCS', 'SINR [dB]'], 
                     dtype={'mode': 'object', 
                            'Time [s]': 'float', 
                            'OFDM symbols': 'int', 
                            'Cell ID': 'int', 
                            'RNTI': 'int', 
                            'CC ID': 'int', 
                            'TB size [bytes]': 'int', 
                            'MCS': 'int', 
                            'SINR [dB]': 'float'}, 
                     engine='python', header=0)
    
    # 按照 ['Cell ID', 'RNTI', 'CC ID', 'UL/DL'] 分组
    grouper = df.groupby(['Cell ID', 'RNTI', 'CC ID', 'UL/DL'])
    sampledDf = pd.DataFrame()
    
    # 对于每个分组，重新采样结果并聚合
    for name, group in grouper: 
        group['Time [s]'] = pd.to_timedelta(group['Time [s]'], unit='s')
        group.set_index('Time [s]', inplace=True)
        
        numeric = group.select_dtypes('number').columns
        non_num = group.columns.difference(numeric)
        d = {**{x: 'mean' for x in numeric}, **{x: 'first' for x in non_num}}

        # 使用 100 毫秒采样时间重新采样数据
        group = group.resample("100ms").agg(d)
        group.reset_index(inplace=True)
        sampledDf = sampledDf.append(group, ignore_index=True)
    
    return sampledDf.values.tolist()

"""
    读取 RxPacketTrace.txt 跟踪文件，使用采样时间 100 毫秒解析它，并返回每个时间段中使用的 OFDM 符号数。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    参数:
        result (str): RxPacketTrace.txt 的内容，类型为字符串
"""
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(['Time [s]', 'OFDM symbols', 'Cell ID', 'RNTI', 
                          'CC ID'])  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*RxPacketTrace.txt')  # 指定只加载某些文件
def calc_ofdm_sym(result):    
    data = []  # 初始化一个空列表以存储解析的值
    df = pd.read_csv(StringIO(result['output']['RxPacketTrace.txt']), 
                     delimiter="\t", index_col=False, 
                     usecols=[0, 1, 6, 7, 8, 9], 
                     names=['UL/DL', 'Time [s]', 'OFDM symbols', 'Cell ID', 
                            'RNTI', 'CC ID'], 
                     dtype={'mode': 'object', 
                            'Time [s]': 'float', 
                            'OFDM symbols': 'int', 
                            'Cell ID': 'int', 
                            'RNTI': 'int', 
                            'CC ID': 'int'}, 
                     engine='python', header=0)
    
    # 按照 ['Cell ID', 'RNTI', 'CC ID'] 分组
    grouper = df.groupby(['Cell ID', 'RNTI', 'CC ID'])
    sampledDf = pd.DataFrame()
    
    # 对于每个分组，重新采样结果并计算使用的 OFDM 符号数
    for name, group in grouper: 
        group['Time [s]'] = pd.to_timedelta(group['Time [s]'], unit='s')
        group.set_index('Time [s]', inplace=True)
        
        # 重新采样并聚合结果，计算使用的 OFDM 符号数
        d = {'OFDM symbols': 'sum', 'Cell ID': 'first', 'RNTI': 'first', 'CC ID': 'first'}
        group = group.resample("100ms").agg(d)
        group.reset_index(inplace=True)
        sampledDf = sampledDf.append(group, ignore_index=True)
    return sampledDf.values.tolist()

"""
    读取 RanAiStats.txt 跟踪文件，解析并返回包含解析值的列表。
    可以作为输入用于 sem 提供的 get_results_as_dataframe 函数。
    参数:
        result (str): RanAiStats.txt 的内容，类型为字符串
"""
@sem.utils.yields_multiple_results  # 声明函数会产生多个结果
@sem.utils.output_labels(['Time [s]',
                          'IMSI',
                          'MCS',
                          'OFDM symbols',
                          'SINR [dB]',
                          'RLC tx pcks',
                          'RLC tx bytes',
                          'RLC rx pcks',
                          'RLC rx bytes',
                          'RLC avg delay',
                          'RLC std delay',
                          'RLC min delay',
                          'RLC max delay',
                          'PDCP tx pcks',
                          'PDCP tx bytes',
                          'PDCP rx pcks',
                          'PDCP rx bytes',
                          'PDCP avg delay',
                          'PDCP std delay',
                          'PDCP min delay',
                          'PDCP max delay',
                          'APP tx pcks',
                          'APP tx bytes',
                          'APP rx pcks',
                          'APP rx bytes',
                          'APP avg delay',
                          'APP std delay',
                          'APP min delay',
                          'APP max delay'
                          ])  # 函数输出的标签
@sem.utils.only_load_some_files(r'.*RanAiStats.txt')  # 指定只加载某些文件
def read_ran_ai(result):
    data = []  # 初始化一个空列表以存储解析的值
    lines = result['output']['RanAiStats.txt'].splitlines()

    for line in lines[1:]:
        values = line.split("\t")
        row = [float(values[0]),
               int(values[1]),
               float(values[2]),
               float(values[3]),
               float(values[4]),
               float(values[5]),
               float(values[6]),
               float(values[7]),
               float(values[8]),
               float(values[9]),
               float(values[10]),
               float(values[11]),
               float(values[12]),
               float(values[13]),
               float(values[14]),
               float(values[15]),
               float(values[16]),
               float(values[17]),
               float(values[18]),
               float(values[19]),
               float(values[20]),
               float(values[21]),
               float(values[22]),
               float(values[23]),
               float(values[24]),
               float(values[25]),
               float(values[26]),
               float(values[27]),
               float(values[28])
               ]
        data += [row]
    return data
