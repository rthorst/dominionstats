#!/usr/bin/python

""" This a mixin to a generically serialize objects to primitive types.

This is serializing the internal variables of classes, and hence is a
big abstraction leak.  By mixing with this class, you can give yourself 
headaches if you change the implementation of a class and want to work
with previously serialized versions of data.
"""

import collections

PRIMITIVES = [dict, str, int, list, float, unicode]

def to_primitive(val):
    if hasattr(val, 'to_primitive_object'):
        return val.to_primitive_object()
    assert type(val) in PRIMITIVES, (val, type(val))
    return val

class PrimitiveConversion(object):
    """ An object that supports the PrimitiveConversion operation can be
    serialized to and deserialized from a possibly nested collection of native
    Python objects.  This requires that all members are either primitives
    or PrimitiveConversions.

    This is useful because they are then easy to turn into mongo BSON objects
    and JSON objects.  

    This default implementation uses self.__dict__ to encode into this object
    into a python dict whose keys are the member names."""
    
    def to_primitive_object(self):
        ret = {}
        for k, v in self.__dict__.iteritems():
            ret[k] = to_primitive(v)
        return ret

    def from_primitive_object(self, obj):
        # Get rid of _id because it's something that mongo injects into our
        # objects, and it's not really natural to the objects themselves.
        obj_keys_except_id = set(obj.keys()) - set(['_id'])
        unicoded_keys = set(map(unicode, self.__dict__.keys()))
        assert unicoded_keys == obj_keys_except_id, (
            '%s != %s' % (str(unicoded_keys),  str(obj_keys_except_id)))
        for k in obj_keys_except_id:
            if hasattr(self.__dict__[k], 'from_primitive_object'):
                self.__dict__[k].from_primitive_object(obj[k])
            else:
                assert type(obj[k]) in PRIMITIVES, obj[k]
                self.__dict__[k] = obj[k]

def _slot_members(inst):
    for member_name in inst.__slots__:
        yield getattr(inst, member_name)

def slot_index_count(obj):
    if isinstance(obj, ListSlotPrimitiveConversion):
        return sum(slot_index_count(member) for member in _slot_members(obj))
    else:
        return 1

class ListSlotPrimitiveConversion(PrimitiveConversion):
    """ A more restrictive, but more compact when serialized version of 
    PrimitiveConversion.  This serializes to/from flat lists.  This
    requires that every member is a Primitive or ListSlotPrimitiveConversion.
    
    Further, every member must define __slots__.  The list indicies 
    depend on the __slots__ ordering, and hence this has trouble 
    (de)serializing versions that contain different slot members, or even
    slot members in different orders.
    """
    
    def to_primitive_object(self):
        ret = [None] * slot_index_count(self)
        self.serialize_to_list(ret, 0)
        return ret

    def from_primitive_object(self, obj):
        assert type(obj) == list
        assert len(obj) == slot_index_count(self), '%d != %d' % (
            len(obj), slot_index_count(self))
                                                                
        self.deserialize_from_list(obj, 0)

    def serialize_to_list(self, l, start):
        for member in _slot_members(self):
            if isinstance(member, ListSlotPrimitiveConversion):
                member.serialize_to_list(l, start)
            else:
                assert type(member) in PRIMITIVES
                l[start] = member
            start += slot_index_count(member)

    def deserialize_from_list(self, l, start):
        for member_name in self.__slots__:
            member_val = getattr(self, member_name)
            if isinstance(member_val, ListSlotPrimitiveConversion):
                member_val.deserialize_from_list(l, start)
            else:
                assert type(member_val) in PRIMITIVES
                setattr(self, member_name, l[start])
            start += slot_index_count(member_val)
                

class ConvertibleDefaultDict(collections.defaultdict, PrimitiveConversion):
    def __init__(self, value_type, key_type = str):
        collections.defaultdict.__init__(self, value_type)
        self.value_type = value_type
        self.key_type = key_type

    def to_primitive_object(self):
        ret = {}
        for key, val in self.iteritems():
            if type(key) == unicode:
                key = key.encode('utf-8')
            else:
                key = str(key)
            ret[key] = to_primitive(val)
        return ret

    def from_primitive_object(self, obj):
        for k, v in obj.iteritems():
            if k == '_id': continue
            val = self.value_type()
            if hasattr(val, 'from_primitive_object'):
                val.from_primitive_object(v)
            else: 
                val = v
            self[self.key_type(k)] = val

if __name__ == '__main__':
    import pymongo
    c = pymongo.Connection()
    db = c.test
    coll = db.prim
    prim_a['_id'] = ''
    coll.save(prim_a, safe='true')

    a_from_db = list(coll.find())[0]
    new_a = A()
    new_a.from_primitive_object(a_from_db)
    assert new_a.foo == a.foo
    assert new_a.bar == a.bar

