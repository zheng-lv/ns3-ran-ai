#!/bin/bash

# 该脚本用于绘制由 three-gpp-vehicular-channel-condition-model-example 生成的轨迹

# 版权声明和许可信息
# 版权所有 (c) 2020年，巴多瓦大学，信息工程系，SIGNET实验室
# 本程序是自由软件；您可以重新分发或修改它
# 根据GNU通用公共许可证第2版的条款发布；
# 本程序是根据GNU通用公共许可证发布的
# 本程序是希望它是有用的，但没有任何担保；
# 即使是适销性或特定用途的暗示保证也没有。
# 更多详细信息，请参见GNU通用公共许可证。
# 您应该已收到GNU通用公共许可证的副本
# 如果没有，请写信给Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# 创建一个名为 'aa' 的文件，其中包含了gnuplot的命令
cat >aa <<EOL
set terminal gif animate delay 100  # 设置输出为动画GIF，每帧之间延迟100毫秒
set output 'map.gif'  # 设置输出文件名为 map.gif
set view map  # 设置视图为地图样式可视化
set style fill transparent solid 0.5  # 设置填充样式为50%不透明度的透明实体
unset key  # 禁用图例
set style fill transparent solid 0.35 noborder  # 设置填充样式为35%不透明度的透明实体，无边框
set style circle radius 5  # 设置默认圆形半径为5

# 循环处理 0 到 90 范围内的数值，为动画生成每一帧
do for [i=0:90] {
  set zrange [i-1:i]  # 设置 z 轴范围，创建动画效果
  set xrange [11.31:11.32]  # 设置 x 轴范围
  set yrange [44.48:44.5]  # 设置 y 轴范围
  set xlabel 'X [m]'  # 设置 x 轴标签
  set ylabel 'Y [m]'  # 设置 y 轴标签
  set xtics  # 启用 x 轴刻度标记
  set ytics  # 启用 y 轴刻度标记

  # 使用 'node-0.gnuplot' 文件中的数据，绘制圆圈，颜色为蓝色
  splot 'node-0.gnuplot' u 2:3:1 with circles lc rgb "blue"
  
  # 创建一个白色矩形，用于隐藏坐标轴和标签
  set object 101 rect from -25,-25 to 1400,1000 fc rgb "white"
}
EOL

# 使用gnuplot执行 'aa' 文件中的命令，并生成地图动画
gnuplot aa

# 删除临时文件 'aa'
rm aa

# rm out.txt
