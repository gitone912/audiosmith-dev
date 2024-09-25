

# Audiosmith Django Project

This project is built using Django. Follow the steps below to set up the project in a virtual environment and run the server.

## Prerequisites

Make sure you have the following installed:

- Python (version 3.x)
- pip (Python package manager)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-directory>
```


2. Create a virtual environment

To create a virtual environment named `audiosmith`, use the following command:

```bash
python -m venv audiosmith
```

### 3. Activate the virtual environment

#### On Windows:

```bash
audiosmith\Scripts\activate
```

#### On macOS/Linux:

```bash
source audiosmith/bin/activate
```

Once activated, your terminal prompt should change to indicate that you're working inside the virtual environment.

### 4. Install the required dependencies

Make sure you are in the project directory where the `requirements.txt` file is located. Then run:

```bash
pip install -r requirements.txt
```

This will install all the necessary packages, including Django, as listed in `requirements.txt`.

### 5. Run Django migrations

Before starting the server, apply the necessary migrations:

```bash
python manage.py migrate
```

### 6. Start the Django development server

Once the migrations are applied, you can start the Django development server:

```bash
python manage.py runserver
```

By default, the server will be accessible at `http://127.0.0.1:8000/`.

### 7. Deactivate the virtual environment (optional)

When you're done working, you can deactivate the virtual environment by running:

```bash
deactivate
```

## Additional Commands

- To create a new Django app within the project:

  ```bash
  python manage.py startapp <app-name>
  ```
- To make new database migrations after making model changes:

  ```bash
  python manage.py makemigrations
  ```
- To apply those migrations:

  ```bash
  python manage.py migrate
  ```

---

Feel free to modify this README file as your project evolves.

```

This will guide users through setting up and running your Django project in a virtual environment. Make sure to replace the `<repository-url>` placeholder with the actual URL to clone the repository.
```
