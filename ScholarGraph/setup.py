"""
ScholarGraph - Personal Knowledge Graph with GraphRAG
"""
from setuptools import setup, find_packages

setup(
    name="ScholarGraph",
    version="0.3.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "neo4j>=5.13.0",
        "pydantic>=2.0.0",
        "python-dotenv",
        "PyPDF2",
        "pypdf",
        "markdown",
        "click",
        "mcp>=0.9.0",
    ],
)
