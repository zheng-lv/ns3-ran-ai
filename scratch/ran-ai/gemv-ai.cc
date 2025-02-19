/*
 * Copyright (c) 2021 SIGNET Lab, Department of Information Engineering,
 * University of Padova
 *
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
 *
 */

#include <fstream>
#include <iomanip>
#include "ns3/core-module.h"
#include "ns3/mobility-module.h"
#include "ns3/gemv-propagation-loss-model.h"
#include "ns3/gemv-tag.h"
#include "ns3/log.h"
#include "ns3/simulator.h"
#include "ns3/network-module.h"
#include "ns3/applications-module.h"
#include "ns3/multi-model-spectrum-channel.h"
#include "ns3/mmwave-helper.h"
#include "ns3/mmwave-point-to-point-epc-helper.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-helper.h"
#include <unistd.h>

#include "ns3/seq-ts-size-frag-header.h"
#include "ns3/bursty-helper.h"
#include "ns3/burst-sink-helper.h"
#include "ns3/bursty-app-stats-calculator.h"
#include "ns3/kitti-trace-burst-generator.h"

using namespace ns3;
using namespace mmwave;

NS_LOG_COMPONENT_DEFINE ("GemvIntegrationExample");

#define MAX_NUM_USERS 50 // maximum number of users

static void
RxBurstCallback (uint32_t nodeId, Ptr<BurstyAppStatsCalculator> statsCalculator, Ptr<const Packet> burst, const Address &from,
         const Address &to, const SeqTsSizeFragHeader &header)
{
  statsCalculator->RxBurst (nodeId, burst, from, to, header);
}

static void
TxBurstCallback (uint32_t nodeId, Ptr<BurstyAppStatsCalculator> statsCalculator, Ptr<const Packet> burst,
                 const Address &from, const Address &to, const SeqTsSizeFragHeader &header)
{
  statsCalculator->TxBurst (nodeId, burst, from, to, header);
}

int
main (int argc, char *argv[])
{
  uint32_t numUes = 1;
  uint32_t firstVehicleIndex = 0;
  uint32_t packetSizeBytes = 20000;
  double ulIpiMicroS = 100e3;
  double dlIpiMicroS = 500e3;
  double bandwidth = 50e6;
  std::string appTracesPath = "../../../input/kitti-dataset.csv";
  std::string gemvTracesPath = "../../../input/bolognaLeftHalfRSU3_50vehicles_100sec/13-May-2021_";
  std::string appType = "kitti";
  uint32_t kittiModel = 1452;
  uint32_t updatePeriodicity = 100;
  uint32_t simDuration = 10;
  double txPower = 23.0;
  bool installRanAI = true;
  bool writeToFile = false;
  bool idealActionUpdate = true;
  bool useFakeRanAi = false;
  bool additionalDelay = true;

  CommandLine cmd;
  cmd.AddValue ("numUes", "Number of UE nodes", numUes);
  cmd.AddValue ("firstVehicleIndex", "Index of the trajectory to be assigned to the first node."
                                     "If there are multiple nodes, subsequent trajectory indeces" 
                                     "will be assigned", firstVehicleIndex);
  cmd.AddValue ("ulIpiMicroS", "Uplink IPI in ms", ulIpiMicroS);
  cmd.AddValue ("dlIpiMicroS", "Downlink IPI in ms", dlIpiMicroS);
  cmd.AddValue ("gemvTracesPath", "Path of the GEMv2 traces", gemvTracesPath);
  cmd.AddValue ("appTracesPath", "The path to the input trace of the application, if applicable.",
                appTracesPath);
  cmd.AddValue ("applicationType", "Uplink application to install in the clients [classic, kitti].", appType);
  cmd.AddValue ("kittiModel", "Compression type [1450, 1451, 1452, 1150]", kittiModel);
  cmd.AddValue ("txPower", "The vehicle tx power in dBm", txPower);
  cmd.AddValue ("updatePeriodicity", "The periodicity of the RAN-AI status update", updatePeriodicity);
  cmd.AddValue ("simDuration", "The duration of the simulation, in seconds", simDuration);
  cmd.AddValue ("installRanAI", "Decide whether or not to install the RAN-AI entity", installRanAI);
  cmd.AddValue ("writeToFile", "Decide whether or not to write PHY, RLC, PDCP and APP stats to file", writeToFile);
  cmd.AddValue ("idealActionUpdate", "Decide whether or not to send a real packet to communicate the action from the RAN-AI", idealActionUpdate);
  cmd.AddValue ("useFakeRanAi", "Use a fake RAN AI", useFakeRanAi);
  cmd.AddValue ("additionalDelay", "True in case you want to account for encoding/decoding delay", additionalDelay);
  cmd.Parse (argc, argv);
  
  Config::SetDefault ("ns3::MmWaveBearerStatsCalculator::AggregatedStats", BooleanValue (true));
  Config::SetDefault ("ns3::MmWaveBearerStatsCalculator::EpochDuration", TimeValue (Seconds (0.1)));
  Config::SetDefault ("ns3::BurstyAppStatsCalculator::EpochDuration", TimeValue (Seconds (0.1)));
  Config::SetDefault ("ns3::KittiTraceBurstGenerator::Model", UintegerValue (kittiModel));
  Config::SetDefault ("ns3::BurstyApplication::EncodingDelay", BooleanValue (additionalDelay));
  Config::SetDefault ("ns3::BurstSink::DecodingDelay", BooleanValue (additionalDelay));
  Config::SetDefault ("ns3::MmWavePhyMacCommon::Bandwidth", DoubleValue (bandwidth));
  Config::SetDefault ("ns3::MmWaveHelper::RlcAmEnabled", BooleanValue (true));
  Config::SetDefault ("ns3::MmWaveHelper::UseIdealRrc", BooleanValue (true));
  Config::SetDefault ("ns3::UdpClient::PacketSize", UintegerValue (packetSizeBytes));
  Config::SetDefault ("ns3::MmWavePhyMacCommon::NumHarqProcess", UintegerValue (100));
  Config::SetDefault ("ns3::LteRlcAm::PollRetransmitTimer", TimeValue (MilliSeconds (100)));
  Config::SetDefault ("ns3::MmWaveUePhy::TxPower", DoubleValue (txPower));
  Config::SetDefault ("ns3::MmWaveEnbNetDevice::StatusUpdate", TimeValue (MilliSeconds(updatePeriodicity)));
  Config::SetDefault ("ns3::MmWaveEnbNetDevice::IdealActionUpdate", BooleanValue (idealActionUpdate));
  Config::SetDefault ("ns3::MmWaveBearerStatsCalculator::WriteToFile", BooleanValue (writeToFile));
  Config::SetDefault ("ns3::BurstyAppStatsCalculator::WriteToFile", BooleanValue (writeToFile));
  if (installRanAI)
    {
      // The following two attributes need to be set to true to avoid conflict in RAN-AI traces and the ones printed in text
      Config::SetDefault ("ns3::MmWaveBearerStatsCalculator::ManualUpdate", BooleanValue (true));
      Config::SetDefault ("ns3::BurstyAppStatsCalculator::ManualUpdate", BooleanValue (true));
    }

  Ptr<GemvPropagationLossModel> gemv = CreateObject<GemvPropagationLossModel> ();

  char buffer[256];
  std::cout << "Current path is " << getcwd (buffer, sizeof (buffer)) << std::endl;
  gemv->SetPath (gemvTracesPath); //该行代码设置了 GEMV 模型的路径，即指定了 GEMV 模型所需要的轨迹文件的路径。这些轨迹文件包含了模拟车辆移动和环境变化的数据，用于模拟实际环境中的信号传播情况。
  Time timeRes = MilliSeconds (100); //这行代码定义了时间分辨率 timeRes，以毫秒为单位。时间分辨率表示 GEMV 模型在仿真中模拟车辆移动和信号变化的时间间隔。
  gemv->SetTimeResolution (timeRes);//该行代码设置了 GEMV 模型的时间分辨率，即将之前定义的时间分辨率应用到 GEMV 模型中，以便在仿真中模拟车辆移动和信号变化的时间间隔。
  Time maxSimTime = gemv->GetMaxSimulationTime (); //这行代码获取了 GEMV 模型的最大仿真时间 maxSimTime，即可以模拟的轨迹数据所涵盖的最长时间段。通常，最大仿真时间由轨迹文件中记录的数据所决定。
  if (Seconds (simDuration) <= maxSimTime)
    {
      maxSimTime = Seconds (simDuration);
    }
  else
    {
      NS_LOG_WARN ("The simulation duration cannot exceed the duration of the traces.");
    }
  gemv->SetAttribute ("IncludeSmallScale", BooleanValue (true));

  std::vector<uint16_t> rsuList = gemv->GetDistinctIds (true);
  std::vector<uint16_t> ueList = gemv->GetDistinctIds (false);

  NS_ABORT_MSG_IF (ueList.size () < numUes, "Too many UEs");
  NS_ABORT_MSG_IF (firstVehicleIndex <= 0, "Vehicle indexes goes from 1 to 50");

  NodeContainer rsuNodes;
  NodeContainer ueNodes;

  for (const auto &i : rsuList)
    {
      // create the RSU node and add it to the container
      Ptr<Node> n = CreateObject<Node> ();
      rsuNodes.Add (n);

      // create the gemv tag and aggrgate it to the node
      Ptr<GemvTag> tag = CreateObject<GemvTag> ();
      tag->SetTagId (i);
      tag->SetNodeType (true);
      n->AggregateObject (tag);
    }
  std::cout << "Number of RSU nodes: " << rsuNodes.GetN () << std::endl;
  NS_ABORT_MSG_IF (rsuNodes.GetN () > 1, "This example works with a single RSU");

  Ptr<UniformRandomVariable> urv = CreateObject<UniformRandomVariable> ();
  uint16_t tagID;

  for (uint32_t i = 0; i < numUes; i++)
  {
    if (i == 0)
    {
      // the ID of the first node (target) is equal to firstVehicleIndex
      tagID = firstVehicleIndex;
      auto it = std::find (ueList.begin (), ueList.end (), tagID);
      ueList.erase (it);
    }
    else if (ueList.size() == 1)
    {
      tagID = ueList.at (0); // when there is only one item, there is no need to drawn an index
    }
    else
    {
      auto id = urv->GetInteger(0, ueList.size()-1);
      tagID = ueList.at (id);
      auto it = std::find (ueList.begin (), ueList.end (), tagID);
      ueList.erase (it);
    }

    NS_LOG_DEBUG ("Add ID " << +tagID << " in position " << +i);
    // create the vehicular node and add it to the container
    Ptr<Node> n = CreateObject<Node> ();
    ueNodes.Add (n);

    // create the gemv tag and aggregate it to the node
    Ptr<GemvTag> tag = CreateObject<GemvTag> ();
    tag->SetTagId (tagID);
    tag->SetNodeType (false);
    n->AggregateObject (tag);
    std::cout << "Node " << i << " has tagID " << tagID << std::endl;
  }

  std::cout << "Number of UE nodes: " << ueNodes.GetN () << std::endl;
  NS_ABORT_MSG_IF (ueNodes.GetN () < 1, "At least one UE is required");

  // Install Mobility Model
  // NB: mobility of vehicular nodes is already taken into account in GEMV traces, we use a constant position mobility model
  // 在 GEMV 轨迹中已经考虑了车辆节点的移动性，我们使用了一个恒定位置的移动性模型
  MobilityHelper mobility;
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (NodeContainer (rsuNodes, ueNodes));
  
  // Manually create a new SpectrumChannel and add the GemvPropagationLossModel 手动创建一个新的光谱通道并添加 Gemv 传播损失模型
  Ptr<MultiModelSpectrumChannel> channel = CreateObject<MultiModelSpectrumChannel> ();
  channel->AddPropagationLossModel (gemv);
  
  // Create the MmWaveHelper and manually set the SpectrumChannel to be used 创建 MmWaveHelper 并手动设置要使用的光谱通道
  Ptr<MmWaveHelper> mmWaveHelper = CreateObject<MmWaveHelper> ();
  Ptr<MmWavePointToPointEpcHelper>  epcHelper = CreateObject<MmWavePointToPointEpcHelper> ();
  mmWaveHelper->SetEpcHelper (epcHelper);
  mmWaveHelper->SetChannel (channel, 0);
  
  Ptr<Node> pgw = epcHelper->GetPgwNode ();

  // Create a single RemoteHost创建单个 RemoteHost
  Ptr<Node> remoteHost = CreateObject<Node> ();
  InternetStackHelper internet;
  internet.Install (remoteHost);

  // Create the Internet
  PointToPointHelper p2ph;
  p2ph.SetDeviceAttribute ("DataRate", DataRateValue (DataRate ("100Gb/s")));
  p2ph.SetDeviceAttribute ("Mtu", UintegerValue (1500));
  p2ph.SetChannelAttribute ("Delay", TimeValue (Seconds (0.010)));
  NetDeviceContainer internetDevices = p2ph.Install (pgw, remoteHost);
  Ipv4AddressHelper ipv4h;
  ipv4h.SetBase ("1.0.0.0", "255.0.0.0");
  Ipv4InterfaceContainer internetIpIfaces = ipv4h.Assign (internetDevices);
  // interface 0 is localhost, 1 is the p2p device 接口0是本地主机，1是 p2p 设备
  Ipv4Address remoteHostAddr = internetIpIfaces.GetAddress (1);

  Ipv4StaticRoutingHelper ipv4RoutingHelper;
  Ptr<Ipv4StaticRouting> remoteHostStaticRouting = ipv4RoutingHelper.GetStaticRouting (remoteHost->GetObject<Ipv4> ());
  remoteHostStaticRouting->AddNetworkRouteTo (Ipv4Address ("7.0.0.0"), Ipv4Mask ("255.0.0.0"), 1);
  
  NetDeviceContainer rsuDevs = mmWaveHelper->InstallSub6EnbDevice (rsuNodes);
  NetDeviceContainer ueDevs = mmWaveHelper->InstallSub6UeDevice (ueNodes);
  
  // Install the IP stack on the UEs 在 UE 上安装 IP 堆栈
  internet.Install (ueNodes);
  Ipv4InterfaceContainer ueIpIface;
  ueIpIface = epcHelper->AssignUeIpv4Address (NetDeviceContainer (ueDevs));
  
  // Assign IP address to UEs, and install applications 将 IP 地址分配给 UE，并安装应用程序
  for (uint32_t u = 0; u < ueNodes.GetN (); ++u)
    {
      Ptr<Node> ueNode = ueNodes.Get (u);
      // Set the default gateway for the UE 设置 UE 的默认网关
      Ptr<Ipv4StaticRouting> ueStaticRouting = ipv4RoutingHelper.GetStaticRouting (ueNode->GetObject<Ipv4> ());
      ueStaticRouting->SetDefaultRoute (epcHelper->GetUeDefaultGatewayAddress (), 1);
    }

  // Attach the UEs to the RSU 将 UE 连接到 RSU
  mmWaveHelper->AttachToClosestEnb (ueDevs, rsuDevs);

  // Install and start applications on UEs and remote host 在 UE 和远程主机上安装和启动应用程序
  uint16_t dlPort = 1000;
  uint16_t ulPort = 2000;
  ApplicationContainer clientApps;
  ApplicationContainer serverApps;
  Ptr<BurstyAppStatsCalculator> statsCalculator = CreateObject<BurstyAppStatsCalculator> ();
  Time ulIpi = MicroSeconds (ulIpiMicroS);
  Time dlIpi = MicroSeconds (dlIpiMicroS);

  std::map<uint16_t, Ptr<Application>> imsiApplication;
  
  for (uint32_t u = 0; u < ueNodes.GetN (); ++u)
    {
      // Set up DL application
      PacketSinkHelper dlPacketSinkHelper ("ns3::UdpSocketFactory",
                                           InetSocketAddress (Ipv4Address::GetAny (), dlPort));
      dlPacketSinkHelper.SetAttribute ("EnableSeqTsSizeHeader", BooleanValue (true));
      serverApps.Add (dlPacketSinkHelper.Install (ueNodes.Get (u)));

      UdpClientHelper dlClient (ueIpIface.GetAddress (u), dlPort);
      dlClient.SetAttribute ("Interval", TimeValue (dlIpi));
      dlClient.SetAttribute ("MaxPackets", UintegerValue (0xFFFFF));

      clientApps.Add (dlClient.Install (remoteHost));

      // Set up UL Application 建立 UL 应用程序

      if (appType == "classic")
        {
          PacketSinkHelper ulPacketSinkHelper ("ns3::UdpSocketFactory",
                                               InetSocketAddress (Ipv4Address::GetAny (), ulPort));
          ulPacketSinkHelper.SetAttribute ("EnableSeqTsSizeHeader", BooleanValue (true));
          serverApps.Add (ulPacketSinkHelper.Install (remoteHost));

          UdpClientHelper ulClient (remoteHostAddr, ulPort);
          ulClient.SetAttribute ("Interval", TimeValue (ulIpi));
          ulClient.SetAttribute ("MaxPackets", UintegerValue (0xFFFFF));

          clientApps.Add (ulClient.Install (ueNodes.Get (u)));
        }
      else if (appType == "kitti")
        {
          // Create bursty application helper
          BurstyHelper burstyHelper ("ns3::UdpSocketFactory",
                                     InetSocketAddress (remoteHostAddr, ulPort));
          burstyHelper.SetAttribute ("FragmentSize", UintegerValue (1200));
          burstyHelper.SetBurstGenerator ("ns3::KittiTraceBurstGenerator", "TraceFile",
                                          StringValue (appTracesPath));
          burstyHelper.SetBurstGenerator ("ns3::KittiTraceBurstGenerator", "Scene",
                                          IntegerValue (urv->GetInteger (1, 9)));
          burstyHelper.SetBurstGenerator ("ns3::KittiTraceBurstGenerator", "ReadingMode",
                                          IntegerValue (1));

          ApplicationContainer appContainer = burstyHelper.Install (ueNodes.Get (u));
          clientApps.Add (appContainer.Get (0));

          // Retrieve node IMSI and add application pointer to map
          auto imsi = DynamicCast<MmWaveUeNetDevice> (ueNodes.Get (u)->GetDevice (0))->GetImsi ();
          imsiApplication.insert (std::make_pair (imsi, appContainer.Get (0)));

          Ptr<BurstyApplication> burstyApp = DynamicCast<BurstyApplication> (appContainer.Get (0)); // obtain the last one inserted
          burstyApp->TraceConnectWithoutContext ("BurstTx", MakeBoundCallback (&TxBurstCallback, ueNodes.Get (u)->GetId (), statsCalculator));

          // Create burst sink helper
          BurstSinkHelper burstSinkHelper ("ns3::UdpSocketFactory",
                                           InetSocketAddress (Ipv4Address::GetAny (), ulPort));
          // Install bursty sink
          serverApps.Add (burstSinkHelper.Install (remoteHost));
          Ptr<BurstSink> burstSink = DynamicCast<BurstSink> (serverApps.Get (serverApps.GetN () - 1)); // obtain the last one inserted

          // Link the burst generator to the bursty sink to process the correct reception delay
          Ptr<KittiTraceBurstGenerator> ktb = DynamicCast<KittiTraceBurstGenerator>(burstyApp->GetBurstGenerator());
          burstSink->ConnectBurstGenerator (ktb);
          // Connect application traces
          burstSink->TraceConnectWithoutContext ("BurstRx", MakeBoundCallback (&RxBurstCallback, imsi, statsCalculator));
        }
      else
        {
          NS_FATAL_ERROR ("Application not supported.");
        }

      ++ulPort;
    }
  
  if (appType == "classic")
  {
    std::cout << "UL APP: UDP | Total UL rate " << packetSizeBytes * 8 / ulIpi.GetSeconds () / 1e6 * numUes << " Mbps" << std::endl;
  }
  else if (appType == "kitti")
  {
    std::cout << "UL APP: kitti | Compression level " << kittiModel << std::endl;
  }
  std::cout << "DL APP: UDP | Total DL rate " << packetSizeBytes * 8 / dlIpi.GetSeconds () / 1e6 * numUes << " Mbps" << std::endl;

  serverApps.Start (MilliSeconds (10));
  clientApps.Start (MilliSeconds (100));
  clientApps.Stop (maxSimTime - Seconds (2.0));
  // Enable trace collection and install RAN-AI on each eNB in the scenario  在场景中启用跟踪收集并在每个 eNB 上安装 RAN-AI
  // This must be done in this order, otherwise the RAN-AI does not receive any information 这必须按照这个顺序完成，否则 RAN-AI 不会接收到任何信息
  mmWaveHelper->EnableRlcTraces ();
  mmWaveHelper->EnablePdcpTraces ();
  if (writeToFile)
    {
      mmWaveHelper->EnableDlPhyTrace ();
      mmWaveHelper->EnableUlPhyTrace ();
    }
  if (installRanAI)
    {
      if (!useFakeRanAi)
      {
        mmWaveHelper->InstallRanAI (rsuDevs, imsiApplication, statsCalculator);        
      }
      else
      {
        // Install a fake RAN AI 安装一个假的 RAN AI
        // In this case, the RAN AI is not created, but the reporting cycle is enabled anyway. The statistics that the gNB sends to the RAN AI are  collected in a file called "RanAiStats.txt".
        // 在这种情况下，RAN AI 没有被创建，但是报告周期还是启用了。GNB 发送给 RAN AI 的统计信息收集在一个名为“ RanAiStats.txt”的文件中。
        // 此选项用于创建脱机训练 RL 代理的数据集
        // This option is used to create a dataset to train the RL agent offline
        mmWaveHelper->InstallFakeRanAI (rsuDevs, imsiApplication, statsCalculator);        
      }
    }

  Time simTime = maxSimTime - Seconds (1.0);
  std::cout << "Max simulation time: " << maxSimTime.GetSeconds () << " s" << "\n";
  std::cout << "Actual simulation time: " << simTime.GetSeconds () << " s" << "\n";
  Simulator::Stop (simTime);
  Simulator::Run ();

  Simulator::Destroy ();
  return 0;
}
  
