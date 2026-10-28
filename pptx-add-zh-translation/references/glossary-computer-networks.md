# 术语表：计算机网络与通信（CST309）

来源："已有" = 用户 L01 笔记（cst309*/L01_introduction_part_1.md）里用过的译法（优先沿用）；"L2" = Lecture 2（物理层）双语课件中确定的译法。新术语追加到对应分组，并注明首次出现的课件与页码。

缩写规则：缩写保留英文，第一次出现写 `中文（缩写）`，之后直接用缩写。

## 基础（沿用 L01）

| English | 中文 | 来源 |
|---|---|---|
| network edge / network core | 网络边缘 / 网络核心 | 已有 |
| end system / host | 端系统 / 主机 | 已有 |
| access network | 接入网络 | 已有 |
| physical media | 物理介质 | 已有 |
| communication link | 通信链路 | 已有 |
| packet | 分组 | 已有 |
| packet switch | 分组交换机 | 已有 |
| router | 路由器 | 已有 |
| bandwidth | 带宽 | 已有 |
| protocol | 协议 | 已有 |
| Ethernet | 以太网 | 已有 |
| head end | 头端（前端汇聚设备） | 已有 |
| ISP | 互联网服务提供商（ISP） | 已有 |
| encapsulation | 封装 | 已有 |

## 数据传输基础（L2）

| English | 中文 | 来源 |
|---|---|---|
| data transmission | 数据传输 | L2 |
| physical layer | 物理层 | L2 |
| signal | 信号 | L2 |
| analog / digital | 模拟 / 数字 | L2 |
| transmitter / receiver | 发送端 / 接收端 | L2 |
| transmission medium (media) | 传输介质 | L2 |
| guided / unguided media | 导向型 / 非导向型介质 | L2 |
| frequency / amplitude / phase | 频率 / 振幅 / 相位 | L2 |
| wavelength | 波长 | L2 |
| period | 周期 | L2 |
| spectrum | 频谱 | L2 |
| attenuation | 衰减 | L2 |
| distortion | 失真 | L2 |
| noise | 噪声 | L2 |
| crosstalk | 串扰 | L2 |
| interference (EMI) | 干扰（电磁干扰 EMI） | L2 |
| modulation / demodulation | 调制 / 解调 | L2 |
| modem | 调制解调器 | L2 |
| encoding | 编码 | L2 |
| data rate / bit rate | 数据速率 / 比特率 | L2 |
| baud rate | 波特率 | L2 |
| simplex / half-duplex / full-duplex | 单工 / 半双工 / 全双工 | L2 |
| serial / parallel transmission | 串行 / 并行传输 | L2 |
| synchronous / asynchronous | 同步 / 异步 | L2 |
| multiplexing (FDM / TDM) | 多路复用（频分 FDM / 时分 TDM） | L2 |

## 传输介质（L2）

| English | 中文 | 来源 |
|---|---|---|
| twisted pair | 双绞线 | L2 |
| UTP / STP | 非屏蔽双绞线（UTP）/ 屏蔽双绞线（STP） | L2 |
| coaxial cable | 同轴电缆 | L2 |
| fiber-optic cable / optical fiber | 光纤电缆 / 光纤 | L2 |
| single-mode / multimode fiber | 单模 / 多模光纤 | L2 |
| core / cladding / jacket | 纤芯 / 包层 / 外护套 | L2 |
| conductor / insulation / shield | 导体 / 绝缘层 / 屏蔽层 | L2 |
| connector (RJ-45) | 连接器（RJ-45） | L2 |
| terrestrial microwave | 地面微波 | L2 |
| satellite (GEO / LEO) | 卫星（地球静止轨道 GEO / 低轨 LEO） | L2 |
| radio / infrared | 无线电 / 红外 | L2 |
| wireless LAN (WLAN) | 无线局域网（WLAN） | L2 |

## 接入与互联（L2）

| English | 中文 | 来源 |
|---|---|---|
| DSL / DSLAM | 数字用户线（DSL）/ DSL 接入复用器（DSLAM） | L2 |
| cable network / cable modem / CMTS | 有线电视网络 / 电缆调制解调器 / 电缆调制解调器端接系统（CMTS） | L2 |
| HFC | 混合光纤同轴（HFC） | L2 |
| FTTH | 光纤到户（FTTH） | L2 |
| splitter | 分离器 / 分光器 | L2 |
| upstream / downstream | 上行 / 下行 | L2 |
| circuit switching | 电路交换 | L2 |
| packet switching | 分组交换 | L2 |
| store-and-forward | 存储转发 | L2 |
| queuing delay / packet loss | 排队时延 / 丢包 | L2 |
| processing / transmission / propagation delay | 处理 / 传输 / 传播时延 | L2 |
| nodal delay | 节点时延 | L2 |
| throughput | 吞吐量 | L2 |
| bottleneck link | 瓶颈链路 | L2 |
| traffic intensity | 流量强度 | L2 |

## L2 新增（各批次实际使用）

| English | 中文 | 来源 |
|---|---|---|
| multiplexer / demultiplexer | 多路复用器 / 多路分解器 | L2 p6 |
| time slot / round-robin | 时隙 / 轮询 | L2 p8 |
| carrier wave | 载波 | L2 p9 |
| phase-shift keying | 相移键控 | L2 p9 |
| big-endian / little-endian | 大端序 / 小端序 | L2 p12 |
| Category 5 / 6 | 5 类线 / 6 类线 | L2 p17 |
| broadband | 宽带 | L2 p18 |
| line-of-sight (LOS) | 视距传输（LOS） | L2 p23 |
| multipath | 多径 | L2 p24 |
| reflection / diffraction / scattering | 反射 / 衍射 / 散射 | L2 p23 |
| band | 频段 | L2 p21 |
| FCC / ITU | 美国联邦通信委员会（FCC）/ 国际电信联盟（ITU） | L2 p21 |
| access point / base station | 接入点 / 基站 | L2 p25/p35 |
| repeater | 中继器 | L2 |
| central office | 中心局 | L2 p29 |
| POTS | 普通老式电话业务（POTS） | L2 p29 |
| last mile | 最后一英里 | L2 |
| subscriber | 用户 | L2 |
| head-end equipment | 头端设备 | L2 p29 |
| DOCSIS | 有线电缆数据服务接口规范（DOCSIS） | L2 p31 |
| FTTx / FTTC / FTTB / FTTN / FTTP | 光纤到 x / 到路边 / 到楼 / 到节点 / 到驻地 | L2 p34 |
| PSTN | 公共交换电话网（PSTN） | L2 p38 |
| call setup / teardown | 呼叫建立 / 拆除 | L2 |
| trunk | 中继线 | L2 |
| buffer | 缓存 | L2 p51 |
| link capacity | 链路容量 | L2 p44 |
| congestion | 拥塞 | L2 |
| kilo / mega / giga / tera | 千 / 兆 / 吉 / 太 | L2 p44 |

## Chapter 1（Part 1 / Part 2）新增（2026-10-08）

"P1" = CST309-Chap1-Introduction，"P2" = CST309-Chap1-Part2，页码为幻灯片页码。

| English | 中文 | 来源 |
|---|---|---|
| PAN / LAN / MAN / WAN | 个人区域网 / 局域网 / 城域网 / 广域网 | P1 p4–8 |
| subnet / transmission line | 子网 / 传输线路 | P1 p8 |
| nuts-and-bolts view / service view | 设备视角 / 服务视角 | P1 p17–20 |
| network of networks | 网络的网络 | P1 p23–31 |
| access ISP / regional ISP / tier-1 ISP | 接入 ISP / 区域 ISP / 一级（tier-1）ISP | P1 p24–31 |
| IXP / peering link | 互联网交换点（IXP）/ 对等互联链路 | P1 p28 |
| content provider network | 内容提供商网络 | P1 p30 |
| protocol suite / network entity | 协议族 / 网络实体 | P1 p32–34 |
| syntax / semantics / timing | 语法 / 语义 / 时序 | P1 p35 |
| protocol stack / reference model | 协议栈 / 参考模型 | P1 p39–41 |
| descriptive / prescriptive model | 描述性 / 规范性模型 | P1 p40 |
| application / transport / network / link / physical layer | 应用层 / 传输层 / 网络层 / 链路层 / 物理层 | P1 p41–46 |
| presentation / session layer | 表示层 / 会话层 | P1 p47 |
| process-to-process / host-to-host / hop-to-hop delivery | 进程到进程 / 主机到主机 / 逐跳交付 | P1 p43–45 |
| demultiplexing（传输层） | 分用 | P1 p45 |
| message / segment / datagram / frame | 报文 / 报文段 / 数据报 / 帧 | P2 p8–14 |
| header（Ht/Hn/Hl） | 首部 | P2 p8–10 |
| encapsulation / decapsulation | 封装 / 解封装 | P1 p54，P2 p12 |
| peers / interface | 对等实体 / 接口 | P1 p56 |
| airplane routing（航空类比） | 飞机航路 | P1 p37，P2 p4 |
| forwarding / routing | 转发 / 路由 | P2 p31 |
| forwarding table / routing algorithm | 转发表 / 路由算法 | P2 p31 |
| bursty data | 突发数据 | P2 p38 |
| caravan analogy / toll booth | 车队类比 / 收费站 | P2 p43 |
| instantaneous / average throughput | 瞬时 / 平均吞吐量 | P2 p46 |
| packet sniffing / IP spoofing / DoS / botnet | 分组嗅探 / IP 欺骗 / 拒绝服务（DoS）/ 僵尸网络 | P2 p51–52 |
| firewall / middlebox | 防火墙 / 中间盒 | P2 p53 |
| packet analyzer / display filter | 分组分析器 / 显示过滤器 | Lab 1 |
| default gateway / subnet mask | 默认网关 / 子网掩码 | Lab 2 |

## Chapter 3 Link Layer（Part 1）新增（2026-10-12）

"C3" = SOF203-Chap3-Link_Layer_-_Part_1.pdf，页码为 PDF 页码。

| English | 中文 | 来源 |
|---|---|---|
| link layer services | 链路层服务 | C3 |
| node / link | 节点 / 链路 | C3 |
| wired / wireless link | 有线 / 无线链路 | C3 |
| framing | 成帧 | C3 |
| link access | 链路接入 | C3 |
| reliable delivery | 可靠交付 | C3 |
| flow control | 流量控制 | C3 |
| error detection / error correction | 差错检测 / 纠错 | C3 |
| bit error | 比特差错 | C3 |
| network interface card (NIC) / adapter | 网络接口卡（NIC）/ 适配器 | C3 |
| MAC address / LAN address / physical address | MAC 地址 / LAN 地址 / 物理地址 | C3 |
| broadcast address | 广播地址 | C3 |
| ARP (Address Resolution Protocol) / ARP table | 地址解析协议（ARP）/ ARP 表 | C3 |
| TTL (time to live) | 生存时间（TTL） | C3 |
| plug-and-play | 即插即用 | C3 |
| Ethernet frame / preamble | 以太网帧 / 前同步码 | C3 |
| CRC (cyclic redundancy check) | 循环冗余校验（CRC） | C3 |
| connectionless / unreliable | 无连接 / 不可靠 | C3 |
| bus / star topology | 总线 / 星型拓扑 | C3 |
| hub | 集线器 | C3 |
| switch / switch table | 交换机 / 交换表 | C3 |
| self-learning | 自学习 | C3 |
| filtering / forwarding / flooding | 过滤 / 转发 / 泛洪 | C3 |
| transparent | 透明的 | C3 |
| collision / collision domain | 碰撞 / 碰撞域 | C3 |
| broadcast domain | 广播域 | C3 |
| VLAN (virtual LAN) / trunk port | 虚拟局域网（VLAN）/ 干线端口 | C3 |
| port-based VLAN | 基于端口的 VLAN | C3 |
| multiple access protocol | 多路访问协议 | C3 |
| broadcast channel / point-to-point link | 广播信道 / 点对点链路 | C3 |
| channel partitioning / random access / taking turns | 信道划分 / 随机接入 / 轮流 | C3 |
| TDMA / FDMA | 时分多址（TDMA）/ 频分多址（FDMA） | C3 |
| slotted ALOHA / pure ALOHA | 时隙 ALOHA / 纯 ALOHA | C3 |
| CSMA / CSMA/CD / CSMA/CA | 载波侦听多路访问（CSMA）/ 带碰撞检测的 CSMA（CSMA/CD）/ 带碰撞避免的 CSMA（CSMA/CA） | C3 |
| carrier sense / collision detection | 载波侦听 / 碰撞检测 | C3 |
| binary (exponential) backoff | 二进制（指数）退避 | C3 |
| polling / token passing | 轮询 / 令牌传递 | C3 |
| efficiency | 效率 | C3 |

## Chapter 3 Link Layer（Part 2 Wireless）新增（2026-10-27）

"C3W" = CST309-Chapter_3_Part_2_LAN_Technologies-Wireless.pptx，页码为幻灯片页码。

| English | 中文 | 来源 |
|---|---|---|
| wireless host / base station / wireless link | 无线主机 / 基站 / 无线链路 | C3W p5–7 |
| network infrastructure | 网络基础设施 | C3W p4 |
| relay | 中继 | C3W p6 |
| backbone link | 主干链路 | C3W p7 |
| hidden terminal problem | 隐藏终端问题（区别：障碍物挡住；signal attenuation 信号衰减是距离太远，两者后果相同） | C3W p9 |
| fading | 衰落 | C3W p23 |
| ad hoc / infrastructure WLAN | 自组织 / 基础设施无线局域网 | C3W p10–12 |
| access point (AP) | 接入点（AP） | C3W p10 |
| association / reassociation | 关联 / 重关联 | C3W p18、p28 |
| SSID / BSSID / ESSID | 服务集标识符 / 基本服务集标识符 / 扩展服务集标识符 | C3W p18–20 |
| BSS / ESS / IBSS | 基本服务集 / 扩展服务集 / 独立基本服务集 | C3W p19–20、p32 |
| roaming | 漫游 | C3W p20 |
| active / passive scanning | 主动 / 被动扫描 | C3W p21–22 |
| probe (request / response) frame | 探测（请求 / 响应）帧 | C3W p21–22 |
| beacon frame | 信标帧 | C3W p18、p21 |
| CSMA/CA (collision avoidance) | 带碰撞避免的载波侦听多路访问（区别：CSMA/CD 是碰撞检测） | C3W p23 |
| random backoff | 随机退避 | C3W p24 |
| DIFS / SIFS | 分布式帧间间隔 / 短帧间间隔 | C3W p25 |
| RTS / CTS | 请求发送 / 允许发送 | C3W p26 |
| defer | 推迟 | C3W p26–27 |
| reservation packet | 预约分组 | C3W p26 |
| management / control / data frame | 管理帧 / 控制帧 / 数据帧 | C3W p28 |
| frame control / duration / seq control / payload | 帧控制 / 持续时间 / 序号控制 / 有效载荷 | C3W p29 |
| more frag / retry / power mgt / more data / Rsvd | 更多分片 / 重试 / 电源管理 / 更多数据 / 保留 | C3W p29 |
| WEP | 有线等效保密（WEP） | C3W p29 |
| RA / TA / DA / SA | 接收方地址 / 发送方地址 / 目的地址 / 源地址（区别：RA/TA 指这一跳，DA/SA 指端点） | C3W p30、p38 |
| To DS / From DS | 去往 DS / 来自 DS | C3W p37–38 |
| DS / WDS | 分布式系统 / 无线分布式系统 | C3W p37–38 |
| 3-/4-addressing mode | 3 地址 / 4 地址模式 | C3W p31 |
