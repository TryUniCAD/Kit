from __future__ import annotations

from Schema import If, P, O, S, Rep, Raw, Cnt, Base, Fn, Until, Emb, C

CURRENT = 19000


def ver(ar):
    v = ar.version
    return CURRENT if not v else v


def Vgt(n, then, other=()):
    return If(lambda s, ar: ver(ar) > n, then, other)


def Vge(n, then, other=()):
    return If(lambda s, ar: ver(ar) >= n, then, other)


def Vlt(n, then, other=()):
    return If(lambda s, ar: ver(ar) < n, then, other)


def Fnz(field, then, other=()):
    return If(lambda s, ar: s[field] != 0, then, other)


def Feq(field, value, then, other=()):
    return If(lambda s, ar: s[field] == value, then, other)


def Fbit(field, mask, then, other=()):
    return If(lambda s, ar: (s[field] & mask) != 0, then, other)


def i32(n):
    return P("i32", n)


def u32(n):
    return P("u32", n)


def u16(n):
    return P("u16", n)


def i16(n):
    return P("i16", n)


def u8(n):
    return P("u8", n)


def f64(n):
    return P("f64", n)


def f32(n):
    return P("f32", n)


def i64(n):
    return P("i64", n)


def time32(n):
    return P("u32", n)


def obj(n):
    return O(n)


def cstr(n):
    return S(n)


def rep(count, name, body):
    return Rep(count, name, body)


def base(cls):
    return Base(cls)


def emb(name, cls):
    return Emb(name, cls)


def cls(name):
    return C(name)


def count(name):
    return Cnt(name)


def u64(n):
    return P("u64", n)


def i8(n):
    return P("i8", n)
