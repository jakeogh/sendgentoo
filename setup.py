from setuptools import find_packages
from setuptools import setup

setup(
    name="sendgentoo",
    version="0.1",
    url="https://github.com/jakeogh/sendgentoo",
    license="MIT",
    author="jakeogh",
    author_email="github.com@v6y.net",
    description="Install Gentoo Linux",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points={
        "console_scripts": [
            "sendgentoosimple = sendgentoo.sendgentoosimple:sendgentoosimple",
            "sendgentoo = sendgentoo.sendgentoo:sendgentoo",
        ],
    },
    classifiers=[
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
    ],
)
