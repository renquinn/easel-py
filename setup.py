import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="easel-cli",
    version="0.0.1",
    author="Ren Quinn",
    author_email="renquinn@gmail.com",
    description="A Canvas course management tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/renquinn/easel-py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPLv3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': ['easel = easel.__main__:main'],
    },
)
