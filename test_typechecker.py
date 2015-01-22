from typechecker import Type, TypeContainer, Pair, Any, get_type, assert_type, TypeCheckError
from pytest import raises


Set = TypeContainer(set)
s2 = Set(int, float)


def test_repr():
    assert repr(Set) == "Set' []", 'repr'
    assert repr(s2) == "Set' [Float' Int']", 'repr'
    assert repr(TypeContainer(tuple)(int, int, str)) == "(Int', Int', Str')"
    assert repr(get_type({1: 'a'})) == "Dict' [Int'=>Str']"


def test_eq():
    assert not Type(int) == Type(float), 'eq'
    assert Type(int) == Type(int), 'eq'
    assert Set != s2, 'ne'
    assert Set == Set(), 'eq'
    assert {Type(int), Type(int)} == {Type(int)}, 'hash'


def test_type_getter():
    assert get_type([]) == TypeContainer(list)
    assert get_type([1]) == TypeContainer(list)(int, int)
    assert get_type('abs') == Type(str)
    assert get_type([[1]]) == TypeContainer(list)(TypeContainer(list)(int)), 'Nested inference'
    assert get_type({1: 'a'}) == TypeContainer(dict)(TypeContainer(Pair)(int, str))


def test_any():
    assert get_type({Any: Any}) == get_type({Any: int})
    assert get_type({int: Any}) == get_type({Any: int})
    assert get_type({Any: 'str'}) != get_type({Any: int})
    assert get_type([Any]) == get_type([int])


def test_pair():
    assert Pair([1, 2]) == Pair(1, 2)
    assert Pair([1, 3]) != Pair(1, 2)

# assert get_type(np.array([]))  # something that doesn't mess up on `== scalar`


def test_deco_exceptions_compile_time():

    def plus(x, y):
        return x + y

    # When passing type info to assert_type, either pass all raw types, all type wrappers or all instances
    # Valid equivalents:
    assert assert_type(int, int)(plus)(3, 4) == 7
    assert assert_type(Type(int), Type(int))(plus)(3, 4) == 7
    assert assert_type(5, 5)(plus)(3, 4) == 7

    # Invalid:
    with raises(TypeCheckError):
        assert_type(Type(int), int)(plus)

    with raises(TypeCheckError):
        assert_type(Type(int), 5)(plus)


def test_deco_exceptions_run_time():
    @assert_type(Type(int), Type(int))
    def plus(x, y):
        return x + y

    @assert_type(int, int)
    def plus2(x, y):
        return x + y

    with raises(TypeCheckError):
        plus('a', 'b')

    assert plus(4, 5) == 9
    assert plus2(1, 2) == 3

    # Type example
    @assert_type({'a': 1}, ret_=1)
    def dct_sum(dct):
        return sum(dct.values())

    assert dct_sum.outtypes == Type(int)
    assert dct_sum.types == [TypeContainer(dict)(TypeContainer(Pair)(str, int))]

    assert assert_type(Any, int)(lambda x, y: y + 1)('derp', 10) == 11

    with raises(TypeCheckError):
        dct_sum({'a': 5, 3: 2})  # ==> TypeError
    assert dct_sum({'a': 5, '3': 2}) == 7

