"""

Due the python bugs:

 - https://bugs.python.org/issue4963
 - https://bugs.python.org/issue1043134
 - https://bugs.python.org/issue6626#msg91205

"""

import mimetypes


def guess_extension(mimetype: str, strict: bool=True) -> str:
    return sorted(mimetypes.guess_all_extensions(mimetype, strict=strict))[0]


def guess_type(url: str, strict: bool=True):
    return mimetypes.guess_type(url, strict=strict)[0]


if __name__ == '__main__':  # pragma: no cover

    print(guess_extension('image/jpeg'))
    print(guess_type('a' + guess_extension('image/jpeg')))

    mimetypes.init()
    print(guess_extension('image/jpeg'))
    print(guess_type('a' + guess_extension('image/jpeg')))

    mimetypes.init()
    print(guess_extension('image/jpeg'))
    print(guess_type('a' + guess_extension('image/jpeg')))

    mimetypes.init()
    print(guess_extension('image/jpeg'))
    print(guess_type('a' + guess_extension('image/jpeg')))
