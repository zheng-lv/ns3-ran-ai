/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include "ns3/core-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("ScratchSimulator");

int 
main (int argc, char *argv[])
{
  NS_LOG_UNCOND ("Scratch Simulator");
  CommandLine cmd;
  cmd.Parse (argc, argv);
}



/*
#include "ns3/core-module.h"：包含了NS-3核心模块的头文件，这些模块提供了网络模拟器的基本功能。
using namespace ns3;：使用了NS-3命名空间，这样可以直接访问NS-3库中的类和函数，而无需每次都指定命名空间。
NS_LOG_COMPONENT_DEFINE ("ScratchSimulator");：定义了日志组件名称为"ScratchSimulator"，用于在NS-3中输出日志。
int main(int argc, char *argv[])：程序的入口函数，接受命令行参数作为输入。
NS_LOG_UNCOND ("Scratch Simulator");：使用NS-3的日志系统输出一条日志消息，表示程序开始执行。
CommandLine cmd;：创建了一个命令行解析器对象，用于解析命令行参数。
cmd.Parse(argc, argv);：解析命令行参数，使得在程序运行时可以传入参数。
该程序本身并未执行具体的网络模拟任务，而是作为一个NS-3模拟器的入口，初始化了日志系统，并提供了命令行参数的解析功能，以便于后续的网络模拟任务的执行和参数设置。
*/
