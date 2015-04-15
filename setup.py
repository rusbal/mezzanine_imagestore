from setuptools import setup, find_packages

setup(
        name = 'imagestore',
        version = '2.7.7',
        packages = find_packages(),
        install_requires = [
            'django',
            'sorl-thumbnail',
            'south',
            'django-autocomplete-light',
            'django-tagging',
            ],
        author = 'Pavel Zhukov',
        author_email = 'gelios@gmail.com',
        description = 'Gallery solution for django projects',
        long_description = open('README.rst').read(),
        license = 'GPL',
        keywords = 'django gallery',
        url = 'https://github.com/hovel/imagestore',
        include_package_data = True
     )
