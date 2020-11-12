import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Py-SCSO-Compare",
    version="1.0",
    author="Maximilian Ernst",
    author_email="mernst32@yahoo.com",
    description="Search and download Java files that contain StackOverflow links from Searchcode, and compare them "
                "with code snippets from StackOverflow questions or answers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mernst32/Py-SCSO-Compare",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
    ],
    python_requires='>=3.6',
)
