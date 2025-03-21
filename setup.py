from setuptools import setup, find_packages

setup(
    name="dsdbench-open",
    version="0.1.0",
    description="Benchmarking LLMs as Data Science Code Debuggers for Multi-Hop and Multi-Bug Errors",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.2",
        "scikit-learn>=1.0.0",
        "snoop>=0.4.0",
        "tenacity>=8.0.0",
        "openai>=1.0.0",
        "tqdm>=4.62.0",
        "jsonlines>=2.0.0",
        "argparse>=1.4.0",
        "pillow>=8.4.0",
    ],
    python_requires=">=3.8",
) 