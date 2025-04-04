# Style Search

Style Search is an AI-powered fashion recommendation platform that leverages advanced image analysis, eBay API integration, and personalized styling technologies to provide intelligent product suggestions.

## Features

- **AI-Powered Style Classification**: Using a hybrid model with ChatGPT-4o vision capabilities, the app can identify and describe any fashion style without being limited to predefined categories.
- **Personalized Recommendations**: Get product recommendations from eBay based on your style analysis.
- **Outfit Combinations**: Receive context-aware outfit suggestions that take into account the current season and weather.
- **User Accounts**: Create an account to save your favorite style predictions and track your fashion history.
- **Detailed Analysis**: Get comprehensive information about your style, including style tags, detailed descriptions, and styling tips.
- **Real-time Feedback**: Provide feedback on prediction accuracy to help improve the system.

## Technologies Used

- **Backend**: Python Flask
- **Database**: PostgreSQL (for user accounts) and MongoDB (for feedback and metadata)
- **Storage**: Backblaze B2 for image storage
- **APIs**: eBay API for product recommendations, OpenAI GPT-4o for AI analysis
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Authentication**: Flask-Login and secure password hashing

## Deployment

### Prerequisites

Before deploying, ensure you have:

1. All required environment variables (see `.env.example` file)
2. A PostgreSQL database
3. A MongoDB database
4. Backblaze B2 storage account
5. eBay API credentials
6. OpenAI API key

### Deployment Options

The application is ready for deployment on various platforms:

- **Render.com** (Recommended): 
  1. Create a new Web Service on Render
  2. Connect your GitHub repository
  3. Choose "Python" as the environment
  4. Set the build command: `pip install -r requirements.txt`
  5. Set the start command: `gunicorn main:app --bind 0.0.0.0:$PORT`
  6. Add all environment variables from `.env.example`
  7. Click "Create Web Service"
- **Heroku**: Follow standard Python app deployment with the included Procfile.
- **DigitalOcean App Platform**: Deploy directly from GitHub with Python runtime configuration.

## Environment Variables

The following environment variables need to be set:

- `OPENAI_API_KEY`: For AI analysis of fashion images
- `DATABASE_URL`: PostgreSQL connection string
- `MONGODB_URI`: MongoDB connection string
- `BACKBLAZE_KEY_ID` and `BACKBLAZE_APPLICATION_KEY`: For cloud storage
- `EBAY_APP_ID`: For product recommendations
- `FLASK_SECRET_KEY`: For session security

## Getting Started

1. Clone this repository
2. Install dependencies with pip
3. Set up environment variables
4. Run the application: `gunicorn main:app`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
