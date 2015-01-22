# typecheck.py
## A simple type checker for python
### Examples

    In [1]: from typechecker import get_type, assert_type
    In [2]: get_type(1)
    Out[2]: Int'
    In [3]: get_type([1, 2])
    Out[3]: List' [Int']
    In [4]: get_type({'a', 1, 2.3})
    Out[4]: Set' [Float' Int' Str']
    In [5]: get_type({'A': 1, 'B': 2})
    Out[5]: Dict' [Str'=>Int']
    In [6]: get_type({'A': 1, 'B': 2, ('C', 3): 4.5})
    Out[6]: Dict' [(Str', Int')=>Float' Str'=>Int']
    In [7]: get_type({'a', 1, 2.3}) == get_type({'a', 1})
    Out[7]: False
    In [8]: get_type({'A': 1, 'B': 2}) == get_type({'A': 1, 'B': 2.3})
    Out[8]: False
    In [9]: get_type({'A': 1, 'B': 2}) == get_type({'abc': -100, 'xyz': 100})
    Out[9]: True
    In [10]: @assert_type(int, int, _ret=[int])
       ....: def plus(x, y):
       ....:         return x + y
       ....:
    In [11]: plus('a', 'b')
    TypeCheckError: Required types [Int', Int'] != (Str', Str')
    In [12]: plus(2, 3)
    Out[12]: 5


See more examples in test file.
