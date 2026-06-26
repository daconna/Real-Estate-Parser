from setuptools import setup, find_packages

setup(
    name="real-estate-kz",
    version="0.1.0",
    description="Real estate market monitoring and analysis system for Kazakhstan (Astana focus)",
    author="daconna",
    author_email="",
    url="https://github.com/daconna/Real-Estate-Parser",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "pandas>=2.1.3",
        "lxml>=4.9.3",
    ],
    entry_points={
        "console_scripts": [
            "real-estate-kz=krisha_parser.__main__:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ],
)
