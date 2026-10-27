# 术语表：统计学习（AIT302）

来源："笔记" = 用户 AIT302 笔记 L01/L02 里的译法（优先沿用）；"已有" = 课件 PDF 里已有的中文。新术语追加到对应分组，并注明首次出现的页码。

缩写规则：缩写保留英文，第一次出现写 `中文（缩写）`，之后直接用缩写。

## 基础

| English | 中文 | 来源 |
|---|---|---|
| statistical learning | 统计学习 | 笔记 |
| statistical reasoning | 统计推理 | 笔记 |
| computing method | 计算方法 | 笔记 |
| data extraction | 数据抽取 | 笔记 |
| future prediction | 未来预测 | 笔记 |
| supervised / unsupervised learning | 监督学习 / 无监督学习 | 笔记 |
| semi-supervised learning | 半监督学习 | 笔记 |
| reinforcement learning | 强化学习 | 笔记 |
| probability law | 概率规律 | 笔记 |
| training data | 训练数据 | 笔记 |
| overfitting | 过拟合 | 笔记 |
| generalizable | 可泛化的 | 笔记 |
| statistically optimal | 统计最优 | 笔记 |
| objective function | 目标函数 | 笔记 |
| data scientist | 数据科学家 | |

## 描述统计

| English | 中文 | 来源 |
|---|---|---|
| descriptive statistics | 描述统计 | 笔记 |
| data collection / presentation / summarization | 数据收集 / 数据呈现 / 数据汇总 | 笔记 |
| statistical commentary | 统计评述 | 笔记 |
| mean (average) | 均值（平均数） | 笔记 |
| median | 中位数 | 笔记 |
| mode | 众数 | 笔记 |
| range | 极差 | 笔记 |
| variance | 方差 | 笔记 |
| standard deviation | 标准差 | 笔记 |
| interquartile range (IQR) | 四分位距（IQR） | 笔记 |
| skewness | 偏度 | 笔记 |
| kurtosis | 峰度 | 笔记 |
| frequency distribution | 频数分布 | |
| histogram | 直方图 | 笔记 |
| percentile | 百分位数 | 笔记 |
| summary table | 汇总表 | 笔记 |
| box plot | 箱线图 | 笔记 |
| frequency polygon | 频率多边形 | 笔记 |
| scatter plot | 散点图 | 笔记 |
| measures of central tendency | 集中趋势度量 | |
| measures of dispersion / variability | 离散程度度量 | |

## 推断统计

| English | 中文 | 来源 |
|---|---|---|
| inferential statistics | 推断统计 | 笔记 |
| population | 总体 | 笔记 |
| sample | 样本 | 笔记 |
| sampling with / without replacement | 有放回抽样 / 无放回抽样 | 已有 p17 |
| simple random / stratified / cluster sampling | 简单随机抽样 / 分层抽样 / 整群抽样 | 已有 p18 |
| estimation | 估计 | 笔记 |
| hypothesis testing | 假设检验 | 笔记 |
| null hypothesis (H0) / alternative hypothesis (Ha) | 原假设（H0）/ 备择假设（Ha） | 已有 p20 |
| parameter / statistic | 参数 / 统计量 | 笔记 |
| analysis of variance (ANOVA) | 方差分析（ANOVA） | 笔记 |
| p-value | p 值 | |
| significance level | 显著性水平 | |
| confidence interval | 置信区间 | |

## 判别分析（Week 2）

| English | 中文 | 来源 |
|---|---|---|
| discriminative / discriminant analysis (DA) | 判别分析（DA） | Week 2 DA p2 |
| linear discriminant analysis (LDA) | 线性判别分析（LDA） | Week 2 |
| non-linear discriminant analysis (NLDA) | 非线性判别分析（NLDA） | Week 2 DA |
| quadratic discriminant analysis (QDA) | 二次判别分析（QDA） | Week 2 DA |
| discriminant function | 判别函数 | Week 2 |
| discriminant score | 判别得分 | Week 2 DA |
| discriminant coefficient / weight | 判别系数 / 权重 | Week 2 DA |
| decision boundary | 决策边界 | Week 2 |
| predictor / independent variable | 预测变量 / 自变量 | Week 2 |
| criterion / dependent variable | 判别标准变量 / 因变量 | Week 2 DA |
| class / group | 类别 / 组 | Week 2 |
| feature space | 特征空间 | Week 2 |
| within-class (within-group) scatter matrix (Sw) | 类内散度矩阵（Sw） | Week 2 LDA |
| between-class (between-group) scatter matrix (SB) | 类间散度矩阵（SB） | Week 2 LDA |
| between-group / within-group sum of squares | 组间平方和 / 组内平方和 | Week 2 DA |
| class mean vector | 类均值向量 | Week 2 LDA |
| covariance matrix | 协方差矩阵 | Week 2 |
| eigenvalue / eigenvector | 特征值 / 特征向量 | Week 2 LDA |
| generalized eigenvalue problem | 广义特征值问题 | Week 2 LDA |
| projection | 投影 | Week 2 LDA |
| dimensionality reduction | 降维 | Week 2 LDA |
| normal distribution | 正态分布 | Week 2 DA |
| kernel function | 核函数 | Week 2 DA |
| linearly separable | 线性可分 | Week 2 DA |
| classification accuracy | 分类准确率 | Week 2 DA |
| probability density function (PDF) | 概率密度函数（PDF） | Week 2 LDA |
| logistic regression | 逻辑回归 | |
| training set / test set | 训练集 / 测试集 | |
| cross-validation | 交叉验证 | |
| scatter matrix | 散度矩阵 | Week 2 LDA |
| class mean | 类均值 | Week 2 LDA |
| separability | 可分性 | Week 2 |
| Fisher's Linear Discriminant (FLD) | Fisher 线性判别分析（FLD） | Week 2 DA p19 |
| unit vector | 单位向量 | Week 2 DA p19 |
| hyperplane | 超平面 | Week 2 DA |
| Small Sample Size (SSS) problem | 小样本量（SSS）问题 | Week 2 DA p13 |
| regularization | 正则化 | Week 2 DA p13 |
| linear combination | 线性组合 | Week 2 DA |
| observation | 观测 | Week 2 DA |
| accuracy / precision / recall | 准确率 / 精确率 / 召回率 | Week 2 |
| missing value / outlier | 缺失值 / 异常值 | Week 2 |
| classifier | 分类器 | Week 2 |
| linear regression | 线性回归 | Week 2 |
| exploratory data analysis (EDA) | 探索性数据分析（EDA） | Week 2 DA |

<!-- AIT302 L03/L04（2026-10）新增术语；来源：课件双语翻译 -->

## 因子分析（Week 3）

| English | 中文 | 来源 |
|---|---|---|
| factor analysis (FA) | 因子分析（FA） | |
| exploratory factor analysis (EFA) | 探索性因子分析（EFA） | |
| confirmatory factor analysis (CFA) | 验证性因子分析（CFA） | |
| factor | 因子 | |
| common factor | 公因子（公共因子） | |
| latent variable | 潜变量 | |
| latent variable model | 潜变量模型 | |
| observed variable | 观测变量 | |
| manifest variable | 显变量 | |
| indicator | 指标 | |
| underlying structure | 潜在结构（底层结构） | |
| principal component analysis (PCA) | 主成分分析（PCA） | |
| principal component | 主成分 | |
| factor extraction | 因子提取 | |
| factor extraction method | 因子提取方法 | |
| factor loading | 因子载荷 | |
| high loading | 高载荷 | |
| factor score | 因子得分 | |
| factor structure | 因子结构 | |
| factor label | 因子命名（因子标签） | |
| factor model | 因子模型 | |
| factor rotation | 因子旋转 | |
| orthogonal rotation | 正交旋转 | |
| oblique rotation | 斜交旋转 | |
| Varimax | 方差最大旋转（Varimax） | |
| Quartimax | 四次方最大旋转（Quartimax） | |
| Equimax | 等量最大旋转（Equimax） | |
| Promax | 斜交最大旋转（Promax） | |
| Direct Oblimin | 直接斜交旋转（Direct Oblimin） | |
| rotation parameter | 旋转参数 | |
| factor space | 因子空间 | |
| group factor | 组因子 | |
| general factor | 一般因子 | |
| multi-vocality | 多因子载荷（变量在多个因子上均有载荷） | |
| Kaiser-Guttman rule | 凯泽-古特曼准则（特征值大于 1 准则） | |
| scree plot | 碎石图 | |
| parallel analysis | 平行分析 | |
| correlation matrix | 相关矩阵 | |
| covariance | 协方差 | |
| shared variance | 共享方差（共同方差） | |
| communality | 共同度 | |
| point of inflexion | 拐点 | |
| Kaiser-Meyer-Olkin (KMO) measure of sampling adequacy | KMO 取样适切性量数（KMO） | |
| Bartlett's test of sphericity | Bartlett 球形检验 | |
| data adequacy | 数据适切性 | |
| sampling adequacy | 取样适切性 | |
| sample size | 样本量 | |
| chi-square statistic | 卡方统计量 | |
| root mean square error of approximation (RMSEA) | 近似误差均方根（RMSEA） | |
| Cronbach's alpha | 克隆巴赫 α 系数 | |
| internal consistency | 内部一致性 | |
| reliability | 信度 | |
| validity / validation | 效度 / 验证 | |
| external criteria | 外部效标 | |
| model fit | 模型拟合 | |
| fit index (fit indices) | 拟合指标 | |
| normality | 正态性 | |
| bell-shaped curve | 钟形曲线 | |
| non-normal data | 非正态数据 | |
| linearity | 线性 | |
| continuous data | 连续数据 | |
| categorical data | 分类数据 | |
| ordinal data | 有序数据 | |
| ordered category | 有序类别 | |
| nominal category | 名义类别 | |
| Likert scale | Likert 量表 | |
| imputation | 插补（填补） | |
| transformation | 变换 | |
| pre-processing | 预处理 | |
| non-linear factor analysis | 非线性因子分析 | |
| data quality | 数据质量 | |
| data exploration | 数据探索 | |
| hypothesis generation | 假设生成 | |
| subjectivity | 主观性 | |
| causal relationship | 因果关系 | |
| causal mechanism | 因果机制 | |

## 回归与正则化（Week 4）

| English | 中文 | 来源 |
|---|---|---|
| regression | 回归 | |
| regression analysis | 回归分析 | |
| regression model | 回归模型 | |
| regression task | 回归任务 | |
| simple linear regression | 简单线性回归 | |
| multiple linear regression | 多元线性回归 | |
| ridge regression | 岭回归 | |
| lasso regression (LASSO) | 套索回归（LASSO） | |
| ordinary least squares (OLS) | 普通最小二乘（OLS） | |
| least squares | 最小二乘 | |
| least squares regression equation | 最小二乘回归方程 | |
| regression equation | 回归方程 | |
| regression line | 回归直线 | |
| best-fit line | 最佳拟合线 | |
| linear relationship | 线性关系 | |
| strength of the relationship | 关系强度 | |
| machine learning algorithm | 机器学习算法 | |
| explanatory variable | 解释变量 | |
| exogenous variable | 外生变量 | |
| response variable | 响应变量 | |
| endogenous variable | 内生变量 | |
| target variable | 目标变量 | |
| intercept | 截距 | |
| y-intercept | y 轴截距 | |
| slope | 斜率 | |
| coefficient | 系数 | |
| regression coefficient | 回归系数 | |
| coefficient estimate | 系数估计（值） | |
| multidimensional space | 多维空间 | |
| point estimate | 点估计 | |
| forecast | 预测（预报） | |
| predicted value | 预测值 | |
| actual value | 实际值 | |
| cost function | 代价函数 | |
| loss function | 损失函数 | |
| gradient descent | 梯度下降 | |
| learning rate | 学习率 | |
| differentiable | 可微的 | |
| underfitting | 欠拟合 | |
| generalize / generalization | 泛化 | |
| generalization performance | 泛化性能 | |
| penalty | 惩罚 | |
| penalty term | 惩罚项 | |
| L1 regularization | L1 正则化 | |
| L2 regularization | L2 正则化 | |
| L1 penalty term | L1 惩罚项 | |
| L2 penalty term | L2 惩罚项 | |
| shrinkage | 收缩 | |
| shrink towards zero | 向零收缩 | |
| tuning parameter | 调优参数 | |
| hyperparameter | 超参数 | |
| regularization parameter | 正则化参数 | |
| regularization strength | 正则化强度 | |
| lambda (λ) | 正则化参数 λ | |
| bias-variance trade-off | 偏差-方差权衡 | |
| bias | 偏差 | |
| multicollinearity | 多重共线性 | |
| collinearity | 共线性 | |
| high-dimensional data | 高维数据 | |
| p >> n problem | p ≫ n 问题（高维小样本） | |
| feature selection | 特征选择 | |
| Elastic Net | 弹性网络（Elastic Net） | |
| sparsity | 稀疏性 | |
| sparse | 稀疏的 | |
| sparse coefficient | 稀疏系数 | |
| sparse model | 稀疏模型 | |
| sparsity ratio | 稀疏率 | |
| L0 norm | L0 范数 | |
| sparse coding | 稀疏编码 | |
| dropout | 随机失活（Dropout） | |
| pruning | 剪枝 | |
| deep learning | 深度学习 | |
| combinatorial optimization problem | 组合优化问题 | |
| standardization / standardize | 标准化 | |
| scale | 尺度（量纲） | |
| variable recoding | 变量重编码 | |
| segmentation | 分割（分组） | |
| data splitting | 数据划分 | |
| validation set | 验证集 | |
| interpretability | 可解释性 | |
| noise | 噪声 | |
| random fluctuation | 随机波动 | |
| model complexity | 模型复杂度 | |
| model parameter | 模型参数 | |
| model fitting | 模型拟合 | |
| predictive power | 预测能力 | |
| prediction error | 预测误差 | |
| unseen data / new data | 未见数据 / 新数据 | |
| unstable / sensitive to inputs | 不稳定的 / 对输入敏感 | |

## 模型评估与诊断（Week 4）

| English | 中文 | 来源 |
|---|---|---|
| model evaluation | 模型评估 | |
| model performance | 模型性能 | |
| assess model fit | 评估模型拟合 | |
| mean squared error (MSE) | 均方误差（MSE） | |
| mean absolute error (MAE) | 平均绝对误差（MAE） | |
| root mean squared error (RMSE) | 均方根误差（RMSE） | |
| sum of squared errors (SSE) | 误差平方和（SSE） | |
| sum of squared prediction error | 预测误差平方和 | |
| residual sum of squares (RSS) | 残差平方和（RSS） | |
| residual standard error (RSE) | 残差标准误（RSE） | |
| R-squared (R²) | 决定系数（R²） | |
| adjusted R-squared | 调整决定系数（调整 R²） | |
| coefficient of determination | 决定系数 | |
| residual | 残差 | |
| residual plot | 残差图 | |
| residual analysis | 残差分析 | |
| independence of errors | 误差独立性 | |
| homoscedasticity | 同方差性 | |
| heteroscedasticity | 异方差性 | |
| funnel shape | 漏斗形 | |
| autocorrelation | 自相关 | |
| serial correlation | 序列相关 | |
| systematic error | 系统误差 | |
| variance inflation factor (VIF) | 方差膨胀因子（VIF） | |
| statistically significant | 统计显著 | |
| standard error | 标准误 | |
| k-fold cross-validation | k 折交叉验证 | |
| leave-one-out cross-validation (LOOCV) | 留一交叉验证（LOOCV） | |
| Akaike information criterion (AIC) | 赤池信息准则（AIC） | |
| Bayesian information criterion (BIC) | 贝叶斯信息准则（BIC） | |
| validation | 验证 | |
| accuracy of prediction | 预测准确度 | |

## 易混词（Week 3–4）

| English | 中文 | 区别 |
|---|---|---|
| factor / component | 因子 / 成分 | 因子分析的"因子"是解释共同方差的潜变量；PCA 的"成分"是观测变量的线性组合，解释总方差 |
| latent variable / observed (manifest) variable | 潜变量 / 观测变量（显变量） | 潜变量不能直接测量，由观测变量推断 |
| loading / score | 载荷 / 得分 | 载荷：变量与因子的关系强度；得分：每个样本在因子上的取值 |
| variance / shared variance / communality | 方差 / 共享方差 / 共同度 | 共同度 = 一个变量的方差中被公因子解释的部分 |
| orthogonal / oblique rotation | 正交旋转 / 斜交旋转 | 正交：旋转后因子互不相关；斜交：允许因子相关 |
| error / residual | 误差 / 残差 | 误差是相对真实模型的偏离（不可观测）；残差 = 实际值 − 拟合值 |
| cost function / loss function | 代价函数 / 损失函数 | 损失针对单个样本，代价是整个训练集上的平均（课件常混用） |
| SSE / RSS / MSE / RSE | 误差平方和 / 残差平方和 / 均方误差 / 残差标准误 | SSE 与 RSS 在本课等价；MSE = SSE/n；RSE = √(RSS/(n−p−1)) |
| R² / adjusted R² | 决定系数 / 调整决定系数 | 调整 R² 对变量个数惩罚，加无用变量不会上升 |
| bias / variance | 偏差 / 方差 | 偏差：模型系统性偏离；方差：换训练集时预测的波动 |
| ridge / lasso / Elastic Net | 岭回归 / 套索回归 / 弹性网络 | L2 / L1 / L1+L2；只有含 L1 的能把系数压到 0（稀疏） |
| regularization / standardization / normalization | 正则化 / 标准化 / 归一化 | 正则化是加惩罚项；标准化 = 减均值除标准差；归一化 = 缩放到固定区间 |
| multicollinearity / collinearity | 多重共线性 / 共线性 | 共线性指两个变量；多重共线性指多个变量间的线性相关 |
| hyperparameter / parameter | 超参数 / 参数 | 超参数（如 λ）训练前设定；参数（如系数）由训练得到 |
| shrinkage / feature selection | 收缩 / 特征选择 | 收缩把系数向 0 拉近；特征选择把部分系数恰好置 0 |
| predict / forecast | 预测 / 预测（预报） | forecast 专指对未来时间点的预测 |

## 时间序列与线性序列分析（Week 5）

| English | 中文 | 来源 |
|---|---|---|
| linear sequence analysis | 线性序列分析 | L5 p1 |
| time series data | 时间序列数据 | L5 p3 |
| stationary time series | 平稳时间序列 | L5 p4 |
| non-stationary time series | 非平稳时间序列 | L5 p4 |
| statistical properties | 统计性质 | L5 p4 |
| step change | 均值阶跃 / 阶跃变化 | L5 p4 |
| shift in variance | 方差变动 | L5 p4 |
| seasonality | 季节性 | L5 p4 |
| random fluctuation | 随机波动 | L5 p4 |
| Augmented Dickey-Fuller (ADF) test | 增广迪基-富勒检验（ADF 检验） | L5 p5 |
| Kwiatkowski-Phillips-Schmidt-Shin Test (KPSS) | KPSS 检验 | L5 p5 |
| unit root | 单位根 | L5 p5 |
| test statistic | 检验统计量 | L5 p5 |
| critical value | 临界值 | L5 p5 |
| autoregressive (AR) model | 自回归模型（AR 模型） | L5 p6 |
| stochastic process | 随机过程 | L5 p9 |
| lag / lagged variable | 滞后 / 滞后变量 | L5 p10 |
| autocorrelation | 自相关 | L5 p10 |
| order (of model, p) | （模型的）阶数（p） | L5 p11 |
| numeric factor / constant | 数值因子 / 常数项 | L5 p11 |
| residual | 残差 | L5 p13 |
| white noise | 白噪声 | L5 p14 |
| positive / negative / zero correlation | 正相关 / 负相关 / 零相关 | L5 p16 |
| vector autoregressive model (VAR) | 向量自回归模型（VAR） | L5 p18 |
| moving average (MA) | 移动平均 / 移动平均模型（MA 模型） | L5 p24 |
| autoregressive integrated moving average (ARIMA) | 自回归积分滑动平均模型（ARIMA） | L5 p3 |
| simple moving average (SMA) | 简单移动平均（SMA） | L5 p27 |
| weighted moving average (WMA) | 加权移动平均（WMA） | L5 p27 |
| exponential moving average (EMA) | 指数移动平均（EMA） | L5 p27 |
| cumulative moving average (CMA) | 累积移动平均（CMA） | L5 p28 |
| smoothing factor / multiplier | 平滑因子 / 乘数 | L5 p36 |
| technical indicator / technical analysis | 技术指标 / 技术分析 | L5 p26 |
| support and resistance | 支撑与阻力（支撑位与阻力位） | L5 p26 |
| trading signal | 交易信号 | L5 p26 |

