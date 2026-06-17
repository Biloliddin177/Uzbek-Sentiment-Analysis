# Uzbek Sentiment Analysis

> A sentiment analysis system for Uzbek-language texts, YouTube comments, and Telegram posts powered by XLM-RoBERTa.

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0-orange?logo=pytorch)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-yellow?logo=huggingface)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red?logo=streamlit)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)

---

##  About

This project fine-tunes **XLM-RoBERTa** on a balanced Uzbek-language dataset to classify text sentiment into three categories:

- 😊 **Positive**
- 😐 **Neutral**
- 😠 **Negative**

---

##  Features

| Feature | Description |
|---|---|
|  Text Analysis | Analyze sentiment of any custom text input |
|  File Upload | Upload `.txt` or `.csv` files for batch analysis |
|  YouTube Analysis | Fetch and analyze YouTube video comments |
|  Telegram Analysis | Analyze posts from Telegram channels |

---

##  Model Performance

| Metric | Score |
|---|---|
| Accuracy | 82% |
| F1-Score | ~81% |
| Precision | ~81% |
| Recall | ~82% |

**Model:** `XLM-RoBERTa` — multilingual transformer fine-tuned on Uzbek sentiment data  
**Dataset:** 47,400 balanced samples (Positive / Neutral / Negative)

---

##  Tech Stack

- **Python** — core programming language
- **PyTorch** — model training and inference
- **HuggingFace Transformers** — XLM-RoBERTa architecture
- **Streamlit** — interactive web interface
- **FastAPI** — backend REST API
- **YouTube Data API** — fetching YouTube comments
- **Telegram API** — fetching Telegram channel posts

---

##  Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Biloliddin177/uzbek-sentiment-analysis.git
cd uzbek-sentiment-analysis
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
YOUTUBE_API_KEY=your_youtube_api_key
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
```

### 4. Run the app

```bash
streamlit run app.py
```

---

##  Project Structure

```
uzbek-sentiment-analysis/
├── app.py              # Streamlit web interface
├── main.py             # Core logic
├── requirements.txt    # Dependencies
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

---

##  Author

**Biloliddin Isomiddinov** — AI/ML specialist

[![GitHub](https://img.shields.io/badge/GitHub-Biloliddin177-black?logo=github)](https://github.com/Biloliddin177)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Biloliddin%20Isomiddinov-blue?logo=linkedin)](https://linkedin.com/in/biloliddin-isomiddinov)
