# Project-Management

This project is built using Streamlit, a python based library useful for rapid creation of applications.

# Project Dependencies

An instance of mySQL is needed to run this application.
Currently XAMPP is used with an apache server to host the DB.

## DB detials should be saved in a file called .env with the following names

DB_HOST
DB_USER
DB_PASSWORD
DB_NAME

## Additionaly a DB should already exist who's name will be the value for DB_NAME

The secret keys related to OpenAI. and the Email/SMTP server should also be stored in a folder in the root directory as `.streamlit` and the file name as `secrets.toml`
`.streamlit/secrets.toml`

# To Get Started

## Install the necessary requirements using

`pip install -r requirements.txt`

## Once the above pre requistes are completed, to start the app run:

`streamlit run app.py`
