# 术语表：计算机体系结构（CST308）

来源："已有" = 课件里用户已用过的译法（优先沿用）；"样稿" = 本 skill 样稿中确定的译法。新术语追加到对应分组，并注明首次出现的页码。

缩写规则：缩写保留英文，第一次出现写 `中文（缩写）`，之后直接用缩写。

## 基础

| English | 中文 | 来源 |
|---|---|---|
| computer architecture | 计算机体系结构 | 已有 p2/p22 |
| instruction set architecture (ISA) | 指令集架构（ISA） | 已有 p22 |
| microarchitecture | 微架构 | 已有 p22 |
| logic design / implementation | 逻辑设计 / 实现 | 已有 p22 |
| system SW | 系统软件 | 已有 p22 |
| programming model | 编程模型 | 已有 p22 |
| motherboard | 主板 | 已有 p9 |
| system unit | 机箱 | 已有 p9 |
| control unit (CU) | 控制单元（CU） | 已有 p10 |
| arithmetic logic unit (ALU) | 算术逻辑单元（ALU） | 已有 p10 |
| register | 寄存器 | 已有 p10 |
| embedded computer | 嵌入式计算机 | 已有 p6 |
| input / output | 输入 / 输出 | 已有 p4 |
| functional unit | 功能单元 | 已有 p23 |
| compiler | 编译器 | 已有 p23 |

## 发展历程

| English | 中文 | 来源 |
|---|---|---|
| generation (of computers) | 代 / 计算机代际 | 已有 p27 |
| vacuum tube | 真空管 | 已有 p28 |
| magnetic drum / magnetic core | 磁鼓 / 磁芯 | 已有 p28, 样稿 p38 |
| transistor | 晶体管 | 已有 p23 |
| integrated circuit | 集成电路 | 已有 p32 |
| semiconductor | 半导体 | 已有 p32 |
| SSI/MSI, LSI/VLSI, ULSI/GSI/WSI | 小/中规模、大/超大规模、特大/巨大/晶圆级集成（缩写保留） | 样稿 p38 |
| SOC (system on chip) | 片上系统（SOC） | 样稿 p38 |
| mainframe / mini / micro | 大型机 / 小型机 / 微型机 | 样稿 p38 |
| machine language / assembly language | 机器语言 / 汇编语言 | 已有 p40 |
| high-level language | 高级语言 | 已有 p25 |

## 功耗与可信赖性（易混词注意区分）

| English | 中文 | 来源 |
|---|---|---|
| dependability | 可信赖性 | 已有 p2 |
| reliability | 可靠性 | 已有 p2/p48 |
| fault | 故障（原因：缺陷） | 已有 p2/p54 |
| error | 错误（故障引起的错误状态） | 已有 p2 |
| failure | 失效（服务偏离规定） | 已有 p2/p48 |
| fault avoidance / detection / tolerance | 故障避免 / 故障检测 / 容错性 | 已有 p54 |
| service level agreement (SLA) | 服务级别协议（SLA） | 已有 p45 |
| service level objective (SLO) | 服务级别目标（SLO） | 已有 p45 |
| service accomplishment / interruption | 服务达成状态 / 服务中断状态 | 已有 p46 |
| time to failure / MTTF | 失效时间 / 平均失效时间（MTTF） | 已有 p48 |
| maintainability / MTTR | 可维护性 / 平均修复时间（MTTR） | 已有 p48 |
| coverage | 覆盖率 | 已有 p48 |
| peak power / voltage droop | 峰值功率 / 电压跌落 | 已有 p41 |

## 性能

| English | 中文 | 来源 |
|---|---|---|
| CPU execution time / CPU time | CPU 执行时间 / CPU 时间 | 样稿 p73 |
| clock cycle / clock cycle time | 时钟周期 / 时钟周期时长 | 样稿 p73 |
| clock rate | 时钟频率 | 样稿 p73 |
| cycles per instruction (CPI) | 每条指令周期数（CPI） | 样稿 p73 |
| instruction count | 指令条数 | 样稿 p73 |

## 定律与数据表示（第 1 章 Part 2 新增）

| English | 中文 | 来源 |
|---|---|---|
| Moore's law | 摩尔定律 | Part2 p4 |
| Amdahl's law | 阿姆达尔定律 | Part2 p2 |
| speedup | 加速比 | Part2 |
| fraction enhanced / speedup enhanced | 可改进部分占比 / 改进部分加速比 | Part2 |
| overall speedup | 总加速比 | Part2 |
| data representation | 数据表示 | Part2 p2 |
| bit / byte / word | 位（比特）/ 字节 / 字 | Part2 |
| binary / octal / decimal / hexadecimal | 二进制 / 八进制 / 十进制 / 十六进制 | Part2 |
| radix / base | 基数 | Part2 |
| sign-magnitude | 原码（符号-数值表示） | Part2 |
| one's complement / two's complement | 反码 / 补码 | Part2 |
| floating point / fixed point | 浮点数 / 定点数 | Part2 |
| exponent / mantissa (significand) | 指数（阶码）/ 尾数 | Part2 |
| overflow | 溢出 | Part2 |
| character encoding / ASCII / Unicode | 字符编码 / ASCII / Unicode（缩写保留） | Part2 |
| MSB / LSB | 最高有效位（MSB）/ 最低有效位（LSB） | Part2 |
| parallelism / parallelizable / parallelization factor | 并行性 / 可并行化 / 并行化因子 | Part2 p11-p27 |
| multicore / MIC / GPU | 多核 / 众核（MIC）/ 图形处理单元（GPU） | Part2 p15 |
| pipelining / superscalar | 流水线 / 超标量 | Part2 |
| power density / diminishing returns | 功率密度 / 收益递减 | Part2 |
| latency / throughput | 延迟 / 吞吐量 | Part2 |
| main memory / cache | 主存 / 高速缓存（cache） | Part2 p11 |
| number system / positional number system | 数制 / 位置计数系统 | Part2 p33, p43 |
| word length / carry / borrow | 字长 / 进位 / 借位 | Part2 |
| bit pattern / coding scheme | 位模式 / 编码方案 | Part2 p42 |
| bitmap / vector image / bit depth / frame | 位图 / 矢量图像 / 位深度 / 帧 | Part2 p52-53 |

## 指令集架构（第 2 章 Part 1 新增）

| English | 中文 | 来源 |
|---|---|---|
| instruction set architecture (ISA) | 指令集架构（ISA） | Ch2 p2 |
| abstraction | 抽象 | Ch2 p2 |
| datapath | 数据通路 | Ch2 p3 |
| control signals | 控制信号 | Ch2 p4 |
| instruction interpreter | 指令解释器 | Ch2 p4 |
| assembly language / assembly code | 汇编语言 / 汇编代码 | Ch2 p6, p11 |
| machine language / machine code | 机器语言 / 机器码 | Ch2 p6, p11 |
| high-level language | 高级语言 | Ch2 p6 |
| compiler / assembler / linker | 编译器 / 汇编器 / 链接器 | Ch2 p6 |
| opcode (operation code) | 操作码（Opcode） | Ch2 p12, p33 |
| source operand | 源操作数 | Ch2 p12, p34 |
| result operand / destination | 结果操作数 / 目的操作数 | Ch2 p12, p34 |
| stack architecture | 堆栈架构 | Ch2 p16, p18 |
| accumulator architecture | 累加器架构 | Ch2 p16, p21 |
| memory-memory architecture | 存储器-存储器架构 | Ch2 p16, p23 |
| register-memory architecture | 寄存器-存储器架构 | Ch2 p16, p24 |
| load-store architecture / register-register | 加载-存储架构（Load-Store 架构）/ 寄存器-寄存器架构 | Ch2 p16, p27 |
| top of stack (TOS) | 栈顶（TOS） | Ch2 p16, p19 |
| push / pop | 压栈（Push）/ 出栈（Pop） | Ch2 p17 |
| LIFO (last in, first out) | 后进先出（LIFO） | Ch2 p17 |
| infix notation / postfix notation | 中缀表达式 / 后缀表达式 | Ch2 p18, p66 |
| general purpose register (GPR) | 通用寄存器（GPR） | Ch2 p30 |
| register file | 寄存器堆 / 寄存器组 | Ch2 p24, p38 |
| RISC (reduced instruction set computer) | 精简指令集计算机（RISC） | Ch2 p52 |
| CISC (complex instruction set computer) | 复杂指令集计算机（CISC） | Ch2 p52 |
| instruction cycle | 指令周期 | Ch2 p56 |
| fetch cycle / execute cycle | 取指周期 / 执行周期 | Ch2 p56 |
| program counter (PC) | 程序计数器（PC） | Ch2 p57 |
| instruction register (IR) | 指令寄存器（IR） | Ch2 p57 |


## MIPS 实验 1（Lab_1_Task）

| English | 中文 | 来源 |
|---|---|---|
| simulator | 模拟器 | Lab1 p1 |
| directive | 伪指令 | Lab1 p2；区别：伪指令由汇编器处理，不同于处理器直接执行的 instruction（指令） |
| data section / text section | 数据段 / 文本段（代码段） | Lab1 p2 |
| global symbol / entry point | 全局符号 / 入口点 | Lab1 p2 |
| system call / syscall | 系统调用 / syscall | Lab1 p2–p3 |
| null-terminated string | 以空字符结尾的字符串 | Lab1 p3 |
| stack pointer / frame pointer | 栈指针 / 帧指针 | Lab1 p1 |
| global pointer / return address | 全局指针 / 返回地址 | Lab1 p1 |
| buffer | 缓冲区 | Lab1 p3 |
