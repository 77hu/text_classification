<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.0+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![NLTK](https://img.shields.io/badge/NLTK-3.8+-154F5B?style=for-the-badge&logo=python&logoColor=white)](https://www.nltk.org/)

</div>

<br/>

<h1 align="center">📝 文本分类实验</h1>

<h3 align="center"><em>机器学习文本分类 · NLP 特征工程 · 多模型对比 · 多策略实验</em></h3>

<br/>

---

## 📖 项目概述

基于传统机器学习方法的文本分类对比实验项目。探索不同**文本表示方法**（TF-IDF / CountVectorizer / Word2Vec）、**特征选择策略**（卡方检验 / 互信息）和**分类算法**（Naive Bayes / SVM / Logistic Regression / Random Forest）在文本分类任务上的性能表现。

### 实验矩阵

| 维度 | 候选方案 |
|------|---------|
| 文本表示 | TF-IDF, CountVectorizer, Word2Vec |
| 特征选择 | Chi-Square, Mutual Information, None |
| 分类器 | Naive Bayes, SVM, Logistic Regression, Random Forest |
| 评估 | Accuracy, Precision, Recall, F1-Score |

### 应用场景

- 垃圾评论自动过滤
- 新闻主题多分类
- 情感极性分析（正面/负面/中性）
- 客服工单自动归档

---

## 🧩 技术路线

```
原始文本
    │
    ▼
┌──────────────────┐
│  文本预处理        │
│  Tokenize + Clean │
│  + 去停用词       │
└────────┬─────────┘
         ▼
┌──────────────────┐
│  特征提取         │
│  TF-IDF / CV /   │
│  Word2Vec        │
└────────┬─────────┘
         ▼
┌──────────────────┐
│  特征选择 (可选)  │
│  Chi2 / MI       │
└────────┬─────────┘
         ▼
┌──────────────────┐
│  模型训练         │
│  NB / SVM / LR / │
│  RF              │
└────────┬─────────┘
         ▼
    评估结果
```

---

## 🚀 快速开始

```bash
git clone https://github.com/77hu/text_classification.git
cd text_classification

pip install scikit-learn nltk pandas numpy

python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

---

## 📄 License

本项目仅供学习和研究使用。
