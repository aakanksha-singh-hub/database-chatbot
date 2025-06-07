from setuptools import setup, find_packages

setup(
    name="db_chatbot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai",
        "pandas",
        "sqlalchemy",
        "pyodbc",
        "python-dotenv",
        "fastapi",
        "uvicorn",
    ],
    python_requires=">=3.9",
) 