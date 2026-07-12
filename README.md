# 文本分类
基于马尔可夫链的城市位置分类器Web应用，Django实现文本输入与城市预测。  
本项目面向文本分类场景，使用Django 5.2.5开发Web应用，基于字符级马尔可夫链转移概率矩阵实现城市位置分类。用户输入一段地址或城市描述文本，系统计算文本在各城市模型下的对数似然，预测最可能的城市。  
项目支持在线预测、历史记录追踪和数据导出API，历经3次数据库迁移迭代。

# 时间表
#### 2025.05.10
初版Django项目搭建，完成fluxclone/tower架构设计  
#### 2025.05.11
完成马尔可夫链分类器实现（predictor.py）  
#### 2025.05.12
完成AttackRecord数据模型和主页视图开发  
#### 2025.05.13
完成0001_initial迁移，创建基础AttackRecord表  
#### 2025.05.14
完成0002迁移，修改session_id字段定义  
#### 2025.05.15
完成0003迁移，增加predicted_cities和prediction_correct字段  
#### 2025.05.16
完成数据导出API接口开发（api_data视图）

# 目录
<a href="#1-项目介绍">1 项目介绍</a>  
- <a href="#关于马尔可夫链分类">1.1 关于马尔可夫链分类</a>  
- <a href="#目录结构">1.2 目录结构</a>  
- <a href="#依赖">1.3 依赖</a>  
- <a href="#算法原理">1.4 算法原理</a>  

<a href="#如何使用">2 如何使用</a>  
- <a href="#安装依赖">2.1 安装依赖</a>  
- <a href="#启动服务">2.2 启动服务</a>  
- <a href="#使用流程">2.3 使用流程</a>  
- <a href="#api接口">2.4 API接口</a>  

<a href="#开发说明">3 开发说明</a>  

<a href="#已知问题">4 已知问题</a>  


# 1 项目介绍
## 1.1 关于马尔可夫链分类
马尔可夫链是一种基于转移概率的随机过程模型。在文本分类中，可以为每个类别（城市）训练一个字符级马尔可夫模型，计算新文本在各模型下的似然分数，选择最高分作为预测类别。

目前常见的文本分类方法对比：

| 方法名称 | 相关要点 |
| ------ | ------ |
| 基于规则（关键词匹配） | 简单但不泛化，无法处理新表达方式 |
| TF-IDF + SVM | 需要大量标注数据，对短文本效果差 |
| 深度学习（LSTM/BERT） | 效果好但需要GPU和大量训练数据 |
| 马尔可夫链 | 本项目采用的方案，轻量级、可解释、适合短文本分类 |

本项目使用**Django Web + 字符级马尔可夫链**方案：
- 每个城市独立训练转移概率矩阵 P(next_char | current_char)
- 使用对数似然计算文本在各城市模型下的得分
- 平滑技术处理零概率问题（默认概率1e-10）

## 1.2 目录结构
| 序号 | 文件名称 | 说明 |
| ------ | ------ | ------ |
| 1 | `manage.py` | Django CLI入口 |
| 2 | `db.sqlite3` | SQLite数据库 |
| 3 | `fluxclone/` | Django项目配置包 |
| 4 | `tower/` | 主应用目录 |
| 5 | `tower/models.py` | AttackRecord数据模型 |
| 6 | `tower/predictor.py` | 马尔可夫链预测引擎 |
| 7 | `tower/views.py` | 视图函数（index + api_data） |
| 8 | `tower/urls.py` | 应用路由 |

## 1.3 依赖
```
pip install "django>=5.2,<6.0"
```

## 1.4 算法原理
```
训练阶段:
  FOR EACH 城市:
    FOR EACH 训练文本:
      FOR EACH 字符对 (char[i], char[i+1]):
        transition_matrix[city][char[i]][char[i+1]] += 1
    归一化转移概率

预测阶段:
  FOR EACH 城市:
    log_likelihood = 0
    FOR EACH 字符对 (char[i], char[i+1]):
      prob = transition_matrix[city].get(char[i], {}).get(char[i+1], 1e-10)
      log_likelihood += log(prob)
    scores[city] = log_likelihood
  返回 max(scores) 对应的城市
```

# 2 如何使用
## 2.1 安装依赖
```
pip install "django>=5.2,<6.0"
```

## 2.2 启动服务
```
python manage.py migrate
python manage.py runserver
```

## 2.3 使用流程
1. 访问主页，输入待分类文本
2. 点击提交，系统调用马尔可夫链分类器
3. 查看预测结果（最可能的城市）

## 2.4 API接口
访问 `/api/data/` 获取所有预测记录的JSON数据：
```json
[
  {
    "input_text": "输入文本",
    "predicted_city": "预测城市",
    "session_id": "会话ID",
    "predicted_cities": "[城市列表JSON]",
    "prediction_correct": true/false,
    "created_at": "时间戳"
  }
]
```

# 3 开发说明
- AttackRecord模型历经3次迁移迭代：
  - 0001：基础字段（input_text + predicted_city + session_id）
  - 0002：修改session_id字段定义
  - 0003：增加predicted_cities（JSON）+ prediction_correct（布尔）
- 使用Django session标记每次预测的会话ID
- 零概率平滑：使用1e-10作为默认概率，避免对数计算溢出

# 4 已知问题
1. 马尔可夫链需要预训练的城市文本数据集，目前训练数据来源需确认
2. 字符级模型对长文本计算量较大，可能需要优化
3. 平滑参数（1e-10）需要根据实际数据调整
4. 缺乏前端可视化展示，目前仅返回文本预测结果
