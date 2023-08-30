r"""
Backrefs for the 'regex' module.

Add the ability to use the following backrefs with re:

 - `\Q` and `\Q...\E`                                           - Escape/quote chars (search)
 - `\c` and `\C...\E`                                           - Uppercase char or chars (replace)
 - `\l` and `\L...\E`                                           - Lowercase char or chars (replace)
 - `\N{Black Club Suit}`                                        - Unicode character by name (replace)
 - `\u0000` and `\U00000000`                                    - Unicode characters (replace)
 - `\R`                                                         - Generic line breaks (search)

Licensed under MIT
Copyright (c) 2015 - 2020 Isaac Muse <isaacmuse@gmail.com>
"""
import regex as _regex
import copyreg as _copyreg
from functools import lru_cache as _lru_cache
from . import util as _util
from . import _bregex_parse
from ._bregex_parse import ReplaceTemplate

__all__ = (
    "expand", "expandf", "match", "fullmatch", "search", "sub", "subf", "subn", "subfn", "split", "splititer",
    "findall", "finditer", "purge", "escape", "D", "DEBUG", "A", "ASCII", "B", "BESTMATCH",
    "E", "ENHANCEMATCH", "F", "FULLCASE", "I", "IGNORECASE", "L", "LOCALE", "M", "MULTILINE", "R", "REVERSE",
    "S", "DOTALL", "U", "UNICODE", "X", "VERBOSE", "V0", "VERSION0", "V1", "VERSION1", "W", "WORD",
    "P", "POSIX", "DEFAULT_VERSION", "FORMAT", "compile", "compile_search", "compile_replace", "Bregex",
    "ReplaceTemplate"
)

# Expose some common re flags and methods to
# save having to import re and backrefs libraries
D = _regex.D
DEBUG = _regex.DEBUG
A = _regex.A
ASCII = _regex.ASCII
B = _regex.B
BESTMATCH = _regex.BESTMATCH
E = _regex.E
ENHANCEMATCH = _regex.ENHANCEMATCH
F = _regex.F
FULLCASE = _regex.FULLCASE
I = _regex.I
IGNORECASE = _regex.IGNORECASE
L = _regex.L
LOCALE = _regex.LOCALE
M = _regex.M
MULTILINE = _regex.MULTILINE
R = _regex.R
REVERSE = _regex.REVERSE
S = _regex.S
DOTALL = _regex.DOTALL
U = _regex.U
UNICODE = _regex.UNICODE
X = _regex.X
VERBOSE = _regex.VERBOSE
V0 = _regex.V0
VERSION0 = _regex.VERSION0
V1 = _regex.V1
VERSION1 = _regex.VERSION1
W = _regex.W
WORD = _regex.WORD
P = _regex.P
POSIX = _regex.POSIX
DEFAULT_VERSION = _regex.DEFAULT_VERSION
escape = _regex.escape

# Replace flags
FORMAT = 1

# Case upper or lower
_UPPER = 1
_LOWER = 2

# Maximum size of the cache.
_MAXCACHE = 500

_REGEX_TYPE = type(_regex.compile('', 0))


@_lru_cache(maxsize=_MAXCACHE)
def _cached_search_compile(pattern, re_verbose, re_version, pattern_type):
    """Cached search compile."""

    return _bregex_parse._SearchParser(pattern, re_verbose, re_version).parse()


@_lru_cache(maxsize=_MAXCACHE)
def _cached_replace_compile(pattern, repl, flags, pattern_type):
    """Cached replace compile."""

    return _bregex_parse._ReplaceParser(pattern, repl, bool(flags & FORMAT)).parse()


def _get_cache_size(replace=False):
    """Get size of cache."""

    if not replace:
        size = _cached_search_compile.cache_info().currsize
    else:
        size = _cached_replace_compile.cache_info().currsize
    return size


def _purge_cache():
    """Purge the cache."""

    _cached_replace_compile.cache_clear()
    _cached_search_compile.cache_clear()


def _is_replace(obj):
    """Check if object is a replace object."""

    return isinstance(obj, ReplaceTemplate)


def _apply_replace_backrefs(m, repl=None, flags=0):
    """Expand with either the `ReplaceTemplate` or compile on the fly, or return None."""

    if m is None:
        raise ValueError("Match is None!")

    if isinstance(repl, ReplaceTemplate):
        return repl.expand(m)
    return _bregex_parse._ReplaceParser(m.re, repl, bool(flags & FORMAT)).parse().expand(m)


def _apply_search_backrefs(pattern, flags=0):
    """Apply the search backrefs to the search pattern."""

    if isinstance(pattern, (str, bytes)):
        re_verbose = VERBOSE & flags
        if flags & V0:
            re_version = V0
        elif flags & V1:
            re_version = V1
        else:
            re_version = 0
        if not (flags & DEBUG):
            p = _cached_search_compile(
                pattern, re_verbose, re_version, type(pattern)
            )
        else:  # pragma: no cover
            p = _bregex_parse._SearchParser(pattern, re_verbose, re_version).parse()
    elif isinstance(pattern, Bregex):
        if flags:
            raise ValueError("Cannot process flags argument with a compiled pattern")
        p = pattern._pattern
    elif isinstance(pattern, _REGEX_TYPE):
        if flags:
            raise ValueError("Cannot process flags argument with a compiled pattern!")
        p = pattern
    else:
        raise TypeError("Not a string or compiled pattern!")
    return p


def _assert_expandable(repl, use_format=False):
    """Check if replace template is expandable."""

    if isinstance(repl, ReplaceTemplate):
        if repl.use_format != use_format:
            if use_format:
                raise ValueError("Replace not compiled as a format replace")
            else:
                raise ValueError("Replace should not be compiled as a format replace!")
    elif not isinstance(repl, (str, bytes)):
        raise TypeError("Expected string, buffer, or compiled replace!")


###########################
# API
##########################
class Bregex(_util.Immutable):
    """Bregex object."""


    __slots__ = ("_pattern", "auto_compile", "_hash")

    def __init__(self, pattern, auto_compile=True):
        """Initialization."""

        super().__init__(
            _pattern=pattern,
            auto_compile=auto_compile,
            _hash=hash((type(self), type(pattern), pattern, auto_compile))
        )

    @property
    def pattern(self):
        """Return pattern."""

        return self._pattern.pattern

    @property
    def flags(self):
        """Return flags."""

        return self._pattern.flags

    @property
    def groupindex(self):
        """Return group index."""

        return self._pattern.groupindex

    @property
    def groups(self):
        """Return groups."""

        return self._pattern.groups

    @property
    def scanner(self):
        """Return scanner."""

        return self._pattern.scanner

    def __hash__(self):
        """Hash."""

        return self._hash

    def __eq__(self, other):
        """Equal."""

        return (
            isinstance(other, Bregex) and
            self._pattern == other._pattern and
            self.auto_compile == other.auto_compile
        )

    def __ne__(self, other):
        """Equal."""

        return (
            not isinstance(other, Bregex) or
            self._pattern != other._pattern or
            self.auto_compile != other.auto_compile
        )

    def __repr__(self):  # pragma: no cover
        """Representation."""

        return '{}.{}({!r}, auto_compile={!r})'.format(
            self.__module__, self.__class__.__name__, self._pattern, self.auto_compile
        )

    def _auto_compile(
        self,
        template,
        use_format=False
    ):
        """Compile replacements."""

        if isinstance(template, ReplaceTemplate):
            if use_format != template.use_format:
                raise ValueError("Compiled replace cannot be a format object!")
        elif isinstance(template, ReplaceTemplate) or (isinstance(template, (str, bytes)) and self.auto_compile):
            return self.compile(template, (FORMAT if use_format and not isinstance(template, ReplaceTemplate) else 0))
        elif isinstance(template, (str, bytes)) and use_format:
            # Reject an attempt to run format replace when auto-compiling
            # of template strings has been disabled and we are using a
            # template string.
            raise AttributeError('Format replaces cannot be called without compiling replace template!')
        return template

    def compile(  # noqa A001
        self,
        repl,
        flags=0
    ):
        """Compile replace."""

        return compile_replace(self._pattern, repl, flags)

    @property
    def named_lists(self):
        """Returned named lists."""

        return self._pattern.named_lists

    def search(
        self,
        string,
        *args,
        **kwargs
    ):
        """Apply `search`."""

        return self._pattern.search(string, *args, **kwargs)

    def match(
        self,
        string,
        *args,
        **kwargs
    ):
        """Apply `match`."""

        return self._pattern.match(string, *args, **kwargs)

    def fullmatch(
        self,
        string,
        *args,
        **kwargs
    ):
        """Apply `fullmatch`."""

        return self._pattern.fullmatch(string, *args, **kwargs)

    def split(
        self,
        string,
        *args,
        **kwargs
    ):
        """Apply `split`."""

        return self._pattern.split(string, *args, **kwargs)

    def splititer(
        self,
        string,
        *args,
        **kwargs
    ):
        """Apply `splititer`."""

        return self._pattern.splititer(string, *args, **kwargs)

    def findall(
        self,
        string,
        *args,
        **kwargs
    ):
        """Apply `findall`."""

        return self._pattern.findall(string, *args, **kwargs)

    def finditer(
        self,
        string,
        *args,
        **kwargs
    ):
        """Apply `finditer`."""

        return self._pattern.finditer(string, *args, **kwargs)

    def sub(
        self,
        repl,
        string,
        *args,
        **kwargs
    ):
        """Apply `sub`."""

        return self._pattern.sub(self._auto_compile(repl), string, *args, **kwargs)

    def subf(
        self,
        repl,
        string,
        *args,
        **kwargs
    ):  # noqa A002
        """Apply `sub` with format style replace."""

        return self._pattern.subf(self._auto_compile(repl, True), string, *args, **kwargs)

    def subn(
        self,
        repl,
        string,
        *args,
        **kwargs
    ):
        """Apply `subn` with format style replace."""

        return self._pattern.subn(self._auto_compile(repl), string, *args, **kwargs)

    def subfn(
        self,
        repl,
        string,
        *args,
        **kwargs
    ):  # noqa A002
        """Apply `subn` after applying backrefs."""

        return self._pattern.subfn(self._auto_compile(repl, True), string, *args, **kwargs)


def compile(  # noqa A001
    pattern,
    flags=0,
    auto_compile=None,
    **kwargs
):
    """Compile both the search or search and replace into one object."""

    if isinstance(pattern, Bregex):
        if auto_compile is not None:
            raise ValueError("Cannot compile Bregex with a different auto_compile!")
        elif flags != 0:
            raise ValueError("Cannot process flags argument with a compiled pattern")
        return pattern
    else:
        if auto_compile is None:
            auto_compile = True

        return Bregex(compile_search(pattern, flags, **kwargs), auto_compile)


def compile_search(pattern, flags=0, **kwargs):
    """Compile with extended search references."""

    return _regex.compile(_apply_search_backrefs(pattern, flags), flags, **kwargs)


def compile_replace(pattern, repl, flags=0):
    """Construct a method that can be used as a replace method for `sub`, `subn`, etc."""

    if pattern is not None and isinstance(pattern, _REGEX_TYPE):
        if isinstance(repl, (str, bytes)):
            if not (pattern.flags & DEBUG):
                call = _cached_replace_compile(pattern, repl, flags, type(repl))
            else:  # pragma: no cover
                call = _bregex_parse._ReplaceParser(pattern, repl, bool(flags & FORMAT)).parse()
        elif isinstance(repl, ReplaceTemplate):
            if flags:
                raise ValueError("Cannot process flags argument with a ReplaceTemplate!")
            if repl.pattern_hash != hash(pattern):
                raise ValueError("Pattern hash doesn't match hash in compiled replace!")
            call = repl
        else:
            raise TypeError("Not a valid type!")
    else:
        raise TypeError("Pattern must be a compiled regular expression!")
    return call


def purge():
    """Purge caches."""

    _purge_cache()
    _regex.purge()


def expand(m, repl):
    """Expand the string using the replace pattern or function."""

    _assert_expandable(repl)
    return _apply_replace_backrefs(m, repl)


def expandf(m, repl):  # noqa A002
    """Expand the string using the format replace pattern or function."""

    _assert_expandable(repl, True)
    return _apply_replace_backrefs(m, repl, flags=FORMAT)


def match(pattern, string, flags=0, *args, **kwargs):
    """Wrapper for `match`."""

    return _regex.match(_apply_search_backrefs(pattern, flags), string, flags, *args, **kwargs)


def fullmatch(pattern, string, flags=0, *args, **kwargs):
    """Wrapper for `fullmatch`."""

    return regex.fullmatch(_apply_search_backrefs(pattern, flags), string, flags, *args, **kwargs)


def search(pattern, string, flags=0, *args, **kwargs):
    """Wrapper for `search`."""

    return _regex.search(_apply_search_backrefs(pattern, flags), string, flags, *args, **kwargs)


def sub(
    pattern,
    repl,
    string,
    count=0,
    flags=0,
    *args,
    **kwargs
):
    """Wrapper for `sub`."""

    is_replace = _is_replace(repl)
    is_string = isinstance(repl, (str, bytes))
    if is_replace and repl.use_format:
        raise ValueError("Compiled replace cannot be a format object!")

    pattern = compile_search(pattern, flags)
    return _regex.sub(
        pattern, (compile_replace(pattern, repl) if is_replace or is_string else repl), string,
        count,
        0,
        *args, **kwargs
    )


def subf(
    pattern,
    repl,
    string,
    count=0,
    flags=0,
    *args,
    **kwargs
):
    """Wrapper for `subf`."""

    is_replace = _is_replace(repl)
    is_string = isinstance(repl, (str, bytes))
    if is_replace and not repl.use_format:
        raise ValueError("Compiled replace is not a format object!")

    pattern = compile_search(pattern, flags)
    rflags = FORMAT if is_string else 0
    return _regex.sub(
        pattern, (compile_replace(pattern, repl, flags=rflags) if is_replace or is_string else repl), string,
        count,
        0,
        *args, **kwargs
    )


def subn(
    pattern,
    repl,
    string,
    count=0,
    flags=0,
    *args,
    **kwargs
):
    """Wrapper for `subn`."""

    is_replace = _is_replace(repl)
    is_string = isinstance(repl, (str, bytes))
    if is_replace and repl.use_format:
        raise ValueError("Compiled replace cannot be a format object!")

    pattern = compile_search(pattern, flags)
    return _regex.subn(
        pattern, (compile_replace(pattern, repl) if is_replace or is_string else repl), string,
        count,
        0,
        *args, **kwargs
    )


def subfn(
    pattern,
    repl,
    string,
    count=0,
    flags=0,
    *args,
    **kwargs
):
    """Wrapper for `subfn`."""

    is_replace = _is_replace(repl)
    is_string = isinstance(repl, (str, bytes))
    if is_replace and not repl.use_format:
        raise ValueError("Compiled replace is not a format object!")

    pattern = compile_search(pattern, flags)
    rflags = FORMAT if is_string else 0
    return _regex.subn(
        pattern, (compile_replace(pattern, repl, flags=rflags) if is_replace or is_string else repl), string,
        count,
        0,
        *args, **kwargs
    )


def split(
    pattern,
    string,
    maxsplit=0,
    flags=0,
    *args,
    **kwargs
):
    """Wrapper for `split`."""

    return _regex.split(_apply_search_backrefs(pattern, flags), string, maxsplit, flags, *args, **kwargs)


def splititer(
    pattern,
    string,
    maxsplit=0,
    flags=0,
    *args,
    **kwargs
):
    """Wrapper for `splititer`."""

    return _regex.splititer(_apply_search_backrefs(pattern, flags), string, maxsplit, flags, *args, **kwargs)


def findall(
    pattern,
    string,
    flags=0,
    *args,
    **kwargs
):
    """Wrapper for `findall`."""

    return _regex.findall(_apply_search_backrefs(pattern, flags), string, flags, *args, **kwargs)


def finditer(
    pattern,
    string,
    flags=0,
    *args,
    **kwargs
):
    """Wrapper for `finditer`."""

    return _regex.finditer(_apply_search_backrefs(pattern, flags), string, *args, **kwargs)


def _pickle(p):
    return Bregex, (p._pattern, p.auto_compile)


_copyreg.pickle(Bregex, _pickle)
