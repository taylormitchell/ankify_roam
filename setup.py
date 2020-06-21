import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ankify_roam", 
    version="0.0.3",
    author="Taylor Mitchell",
    author_email="taylor.j.mitchell@gmail.com",
    description="A command-line tool for importing flashcards from Roam into Anki",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/taylormitchell/ankify_roam",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts":[
            "ankify_roam=ankify_roam.actions:cli"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
