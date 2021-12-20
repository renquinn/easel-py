import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as fh:
    install_requires = fh.read().splitlines()

setuptools.setup(
    name="easel-cli",
    version="1.0.3",
    author="Ren Quinn",
    author_email="renquinn@gmail.com",
    description="A Canvas course management tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/renquinn/easel-py",
    install_requires=install_requires,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': ['easel = easel.__main__:main'],
    },
)
