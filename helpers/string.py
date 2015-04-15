def reverse_slug(string, remove_extension=False, title=False):
    if remove_extension:
        string = ' '.join(string.split('.')[:-1])

    string = ' '.join(string.split('-'))
    string = ' '.join(string.split('_'))
    string = ' '.join(string.split())

    if title:
        string = string.title()
    return string
