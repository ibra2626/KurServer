from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="kurserver",
    version="0.1.0",
    author="KurServer Development Team",
    author_email="dev@kurserver.com",
    description="Ubuntu sunucular için web sunucusu yönetim CLI aracı",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/kurserver",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "kurserver=kurserver.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "kurserver": [
            "config/templates/*.j2",
            "templates/**/*.j2",
        ],
    },
)