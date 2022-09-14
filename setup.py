import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="libphpphar",
    version="0.0.1-alpha",
    author="Frank",
    author_email="frankli0324@hotmail.com",
    description="generate PHP phar archives on the fly",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/frankli0324/libphpphar",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.7',
    install_requires=[]
)
