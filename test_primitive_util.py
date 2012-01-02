#!/usr/bin/python

import unittest
import primitive_util

class SimpleConversion(unittest.TestCase):
    def test(self):
        class A(primitive_util.PrimitiveConversion):
            def __init__(self):
                self.foo = int()
                self.bar = str()

        a = A()
        a.foo = 3
        a.bar = 'baz'

        prim_a = a.to_primitive_object()
        returned_a = A()
        returned_a.from_primitive_object(prim_a)

        self.assertEquals(returned_a.foo, a.foo)
        self.assertEquals(returned_a.bar, a.bar)

class ConvertibleDefaultDictTest(unittest.TestCase):
    def test(self):
        a = primitive_util.ConvertibleDefaultDict(str)
        a['foo'] = 3
        
        prim_a = a.to_primitive_object()
        returned_a = primitive_util.ConvertibleDefaultDict(str)
        returned_a.from_primitive_object(prim_a)
        self.assertEquals(a, returned_a)

    def testNestedCDD(self):
        CDD = primitive_util.ConvertibleDefaultDict
        x = CDD(value_type = lambda: CDD(value_type = int))
        x['foo']['bar'] = 2
        
        prim_x = x.to_primitive_object()
        self.assertEquals(prim_x, {'foo': {'bar': 2}})
        returned_x = CDD(value_type = lambda: CDD(value_type = int))
        returned_x.from_primitive_object(prim_x)
        self.assertEquals(x, returned_x)

class NestedClassPrimTest(unittest.TestCase):
    def test(self):
        class B(primitive_util.PrimitiveConversion):
            def __init__(self):
                self.foo = int()

        class A(primitive_util.PrimitiveConversion):
            def __init__(self):
                self.d = primitive_util.ConvertibleDefaultDict(B)

        a = A()
        a.d['1'].foo = 1
        a.d['2'].foo = 4

        prim_a = a.to_primitive_object()
        returned_a = A()
        returned_a.from_primitive_object(prim_a)

        self.assertEquals(a.d['1'].foo, returned_a.d['1'].foo)
        again_prim_a = returned_a.to_primitive_object()
        self.assertEquals(prim_a, again_prim_a)

class ListSlotPrimTest(unittest.TestCase):
    def test(self):
        class F(primitive_util.ListSlotPrimitiveConversion):
            __slots__ = ('f1', 'f2')

            def __init__(self):
                self.f1 = 0
                self.f2 = 0

        class G(primitive_util.ListSlotPrimitiveConversion):
            __slots__ = ('g1', 'g2')
            
            def __init__(self):
                self.g1 = F()
                self.g2 = F()

        self.assertEquals(primitive_util.slot_index_count(int()), 1)
        self.assertEquals(primitive_util.slot_index_count(F()), 2)
        self.assertEquals(primitive_util.slot_index_count(G()), 4)

        g = G()
        g.g1.f1 = 1
        g.g1.f2 = 2
        g.g2.f1 = 3
        g.g2.f2 = 5
        prim_g = g.to_primitive_object()
        self.assertEquals(prim_g, [1,2,3,5])
        new_g = G()
        new_g.from_primitive_object(prim_g)
        self.assertEquals(new_g.g1.f1, 1)
        self.assertEquals(new_g.g1.f2, 2)
        self.assertEquals(new_g.g2.f1, 3)
        self.assertEquals(new_g.g2.f2, 5)


if __name__ == '__main__':
    unittest.main()
