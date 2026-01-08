"""
Setup configuration for llmobserve SDK.
"""
from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="llmobserve-sdk",
    version="0.3.0",
    author="Pranav Srigiriraju",
    author_email="support@llmobserve.com",
    description="Automatic cost tracking and observability for LLM applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/llmobserve",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/llmobserve/issues",
        "Documentation": "https://docs.llmobserve.com",
        "Source Code": "https://github.com/yourusername/llmobserve",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "llmobserve=llmobserve.cli:main",
        ],
    },
    keywords="llm observability cost tracking openai anthropic monitoring",
    include_package_data=True,
    zip_safe=False,
)









