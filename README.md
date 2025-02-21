# YatraHub 🛫

A comprehensive travel planning platform designed to help you plan your perfect trip or pilgrimage.

## Features ✨

- Personalized trip planning
- Pilgrimage route optimization
- Accommodation recommendations
- Sacred site information
- Travel itinerary generation
- Budget management
- Weather forecasts
- Local transport details

## Getting Started 🚀

1. Create your account
2. Enter your destination details
3. Start planning your journey

## Setup Guide 🛠️

### Prerequisites
- Python 3.8 or higher
- Git
- Google Cloud account for Gemini API

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/yatrahub.git
cd yatrahub
```

2. Create virtual environment (requires Python 3.12.7):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### API Configuration

1. Get Gemini API key:
    1. Get Gemini API key:
        - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
        - Create new project
        - Generate API key
        - Save key in `.env` file:
          ```
          GEMINI_API_KEY=your_key_here
          ```

### Running the App

```bash
python app.py
```