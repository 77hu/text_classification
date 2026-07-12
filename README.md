<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.0+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![NLP](https://img.shields.io/badge/NLP-Text_Classification-154F5B?style=for-the-badge&logo=python&logoColor=white)](https://www.nltk.org/)

</div>

<br/>

<h1 align="center">📝 文本分类系统</h1>

<h3 align="center"><em>机器学习文本分类 · NLP 特征工程 · 多模型对比实验</em></h3>

<br/>

---

## 📑 目录

- [📖 项目概述](#-项目概述)
- [🧩 技术路线](#-技术路线)
- [🚀 快速开始](#-快速开始)
- [📊 实验对比](#-实验对比)
- [📁 项目结构](#-项目结构)

---

## 📖 项目概述

基于传统机器学习方法的文本分类实验项目，探索不同特征工程策略和分类算法在文本分类任务上的表现。

### 应用场景

| 场景 | 说明 |
|------|------|
| 垃圾评论过滤 | 识别低质量/垃圾评论 |
| 情感极性分类 | 正面/负面/中性情感识别 |
| 主题分类 | 多类别文档自动归类 |

---

## 🧩 技术路线

| 环节 | 可选方案 |
|------|---------|
| 文本表示 | TF-IDF / CountVectorizer / Word2Vec |
| 特征选择 | Chi-Square / Mutual Information |
| 分类器 | Naive Bayes / SVM / Logistic Regression / Random Forest |
| 评估 | Accuracy / Precision / Recall / F1-Score |

---

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/77hu/text_classification.git
cd text_classification

# 2. 安装依赖
pip install scikit-learn nltk pandas numpy

# 3. 下载 NLTK 数据
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

---

## 📊 实验对比

| 模型 | 准确率 | 精确率 | 召回率 | F1 |
|------|--------|--------|--------|-----|
| Naive Bayes | — | — | — | — |
| SVM | — | — | — | — |
| Logistic Regression | — | — | — | — |
| Random Forest | — | — | — | — |

---

## 📁 项目结构

```
📦 text_classification/
└── 📘 README.md              # 本文档
```

---

## 📄 License

本项目仅供学习和研究使用。
