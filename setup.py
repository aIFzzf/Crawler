from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="quant-crawler",  # 包名称
    version="0.1.0",       # 版本号
    author="neozfzheng",    # 作者名
    author_email="your.email@example.com",  # 作者邮箱
    description="A powerful crawler framework for quantitative analysis",  # 简短描述
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/quant-crawler",  # 项目URL
    packages=find_packages(exclude=["tests*", "examples*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
)
