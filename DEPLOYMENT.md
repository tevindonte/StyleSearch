# Style Search Deployment Guide

This guide covers the steps to deploy Style Search to various cloud platforms.

## Prerequisites

Before deploying, ensure you have:

1. All required environment variables (see `.env.example` file)
2. A PostgreSQL database
3. A MongoDB database
4. Backblaze B2 storage account
5. eBay API credentials
6. OpenAI API key

## Deployment Options

### 1. Render.com (Recommended)

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Choose "Python" as the environment
4. Set the build command: `pip install -r requirements.txt`
5. Set the start command: `gunicorn main:app`
6. Add all environment variables from `.env.example`
7. Click "Create Web Service"

### 2. Heroku

1. Install the Heroku CLI
2. Login to Heroku: `heroku login`
3. Create a new Heroku app: `heroku create style-search`
4. Push to Heroku: `git push heroku main`
5. Set environment variables:
   ```
   heroku config:set FLASK_SECRET_KEY=your_secret_key
   heroku config:set DATABASE_URL=your_database_url
   heroku config:set MONGODB_URI=your_mongodb_uri
   heroku config:set OPENAI_API_KEY=your_openai_api_key
   heroku config:set BACKBLAZE_KEY_ID=your_backblaze_key_id
   heroku config:set BACKBLAZE_APPLICATION_KEY=your_backblaze_application_key
   heroku config:set EBAY_APP_ID=your_ebay_app_id
   ```
6. Open the app: `heroku open`

### 3. DigitalOcean App Platform

1. Log in to your DigitalOcean account
2. Go to the App Platform section
3. Click "Create App" and select your GitHub repository
4. Choose "Python" as the environment
5. Set the run command: `gunicorn main:app`
6. Set all environment variables from `.env.example`
7. Select a plan and deploy

## Database Migrations

The application will automatically create the necessary tables when it first runs. However, if you need to make database schema changes in the future, you'll need to follow these steps:

1. Connect to your database using a SQL client
2. Make your schema changes carefully
3. Update the corresponding models in the application code

## Troubleshooting

If you encounter issues during deployment:

1. Check the application logs for errors
2. Verify all environment variables are set correctly
3. Ensure the database connection strings are correct
4. Check the Backblaze B2 credentials and bucket permissions
5. Verify the eBay API credentials are valid

For additional help, please refer to the documentation for your chosen deployment platform.