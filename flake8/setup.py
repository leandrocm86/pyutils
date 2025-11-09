from setuptools import setup, find_packages

setup(
    name="flake8-var-final",
    version="0.1.1",
    description="flake8 plugin to enforce var_ prefix for mutable variables",
    author="Leandro Medeiros",
    packages=find_packages(),
    install_requires=["flake8>=6.0.0"],
    entry_points={
        'flake8.extension': [
            'VAR001 = flake8_var_final:VarFinalChecker',
        ],
    },
    classifiers=[
        "Framework :: Flake8",
        "Programming Language :: Python :: 3",
    ],
)