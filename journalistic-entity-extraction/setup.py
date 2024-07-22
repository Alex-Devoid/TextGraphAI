from setuptools import setup, find_packages

setup(
    name="journalistic_entity_extraction",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "py2neo",
        "python-dotenv"
    ],
    entry_points={
        'console_scripts': [
            'journalistic_entity_extraction=journalistic_entity_extraction.main:app',
        ],
    },
)
