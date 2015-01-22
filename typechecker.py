from functools import wraps
import operator as op


class TypeCheckError(TypeError):
    pass


def type_assertion(cond, error, msg=''):
    if not cond:
        raise error(msg)
    return True


def assert_type(*types, **kw):
    """
    `*tps`: types that function should accept
    keywords:
    @ret_: return type that function should have
    @at_least: minimum args decorated function should have
    TODO: any other: types that kwargs should have
    """

    raw_types = map(type, types)
    all_raw = map(lambda x: x == type, raw_types)
    # all_raw = map(lambda x: isinstance(x, type), raw_types)

    w = 'Either all of `types` should be raw, or none should be'
    type_assertion(all(all_raw) or not any(all_raw), TypeCheckError, w)

    # all_typed = map(lambda t: isinstance(t, Type), raw_types)
    all_typed = map(lambda t: isinstance(t, Type), types)
    w = 'Either all of `types` should be instance of Type, or none should be'
    type_assertion(all(all_typed) or not any(all_typed), TypeCheckError, w)

    if not all(all_typed):
        types = map(get_type, types)
    at_least = kw.pop('nlt', 0)
    at_most = kw.pop('ngt', float('inf'))
    exp_ret_type = kw.pop('ret_', None)
    if exp_ret_type is not None:
        exp_ret_type = get_type(exp_ret_type) if not isinstance(exp_ret_type, Type) else exp_ret_type

    def deco(f):
        @wraps(f)
        def wrapped(*a, **kw):
            w = '{} needs at least {} args. {} passed.'.format(f.__name__, at_least, len(a))
            type_assertion(len(a) >= at_least, TypeCheckError, w)

            w = '{} needs no more than {} args. {} passed.'.format(f.__name__, at_most, len(a))
            type_assertion(len(a) <= at_most, TypeCheckError, w)

            in_types = tuple(map(get_type, a))
            eqs = map(op.eq, types, in_types)
            w = 'Required types {} != {}'.format(types, in_types)
            type_assertion(all(eqs), TypeCheckError, w)

            res = f(*a, **kw)

            # Check return type
            if exp_ret_type is not None:
                ret_type = get_type(res)
                assert exp_ret_type == ret_type, 'Required return type {} != {}'.format(exp_ret_type, ret_type)
            return res
        wrapped.types = types
        wrapped.outtypes = exp_ret_type
        return wrapped

    return deco


class Any(type):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


class Type(object):
    def __init__(self, typ):
        assert isinstance(typ, type) or typ == Any
        self.typ = typ
        if typ not in Type._type_list:
            Type._type_list[typ] = self

    def __hash__(self):
        return hash(self.typ)

    def __cmp__(self, other):
        return cmp(self.typ, other.typ)

    def __repr__(self):
        if hasattr(self.typ, '__name__'):
            return self.typ.__name__.capitalize() + "'"
        return self.__class__.__name__ + "'"

    def type_repr(self, x):
        if isinstance(x, type):
            return x.__name__
        return repr(x)

    def __eq__(self, other):
        same_type = type(self) == type(other)
        anys = self.typ == other.typ or Any in {self.typ, other.typ}
        return same_type and anys

        if hasattr(self, 'typ'):
            return self.typ.__name__.capitalize() + "'"
        return self.__class__.__name__ + "'"

    def __ne__(self, other):
        return not self.__eq__(other)

    _type_list = {}  # TODO: Function to register new items on the fly


class TypeContainer(Type):
    def __init__(self, typ):
        super(self.__class__, self).__init__(typ)
        self.ordered = typ in {tuple, Pair}
        self.cont_holder = tuple if self.ordered else (lambda x: sorted(set(x)))

    def copy(self):
        new_self = self.__class__(self.typ)
        return new_self

    def __call__(self, *args):  # TODO: return copy of self that isn't callable
        assert all([isinstance(a, (type, Type)) for a in args]), 'Must only pass bare types'
        ensure_type = lambda x: Type(x) if not isinstance(x, Type) else x
        new_self = self.copy()
        new_self.cont_types = self.cont_holder(map(ensure_type, args))
        return new_self

    def __repr__(self):
        conts = getattr(self, 'cont_types', [])
        if self.typ == Pair:
            k, v = conts
            return '{}=>{}'.format(k, v)
        if self.typ == tuple:
            return '({})'.format(', '.join(map(self.type_repr, conts)))
        base_r = super(self.__class__, self).__repr__()
        return '{} [{}]'.format(base_r, ' '.join(map(self.type_repr, conts)))

    def __eq__(self, other):
        base_eq = super(self.__class__, self).__eq__(other)
        return base_eq and (self.cont_types == other.cont_types)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.typ) + hash(tuple(self.cont_types))

    cont_types = []


class Pair(tuple):
    "Use for representation of dict types"
    def __new__(cls, *a):
        try:
            if len(a) == 2:
                k, v = a
            else:
                k, v = a[0]
        except ValueError:
            raise ValueError('Pairs only allow for 2 values')
        return super(Pair, cls).__new__(cls, (k, v))


def get_type(x):
    if isinstance(x, Type):
        return x
    if isinstance(x, (str, unicode, file)):
        return Type(type(x))
    if isinstance(x, type):
        return Type(x)
    if not hasattr(x, '__iter__') and x == Any:
        return Type(x)

    try:  # container type
        _dct = isinstance(x, dict)
        iter_ = (lambda x: map(Pair, x.items())) if _dct else iter

        type_wrapper = TypeContainer(type(x))
        cont_types = type_wrapper.cont_holder(map(get_type, iter_(x)))
        # TODO: special `iter` infinite lists
        return type_wrapper(*cont_types)
    except (TypeError, KeyError):  # KeyError: redis.client tries to iterate by giving self wrong key
        return Type(type(x))

