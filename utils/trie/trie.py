
from pickle import dumps, loads

from utils.crypto.hash import sha3_hex
from .base import BaseTrie

from .util import (
    hex_to_nibbles, decode_type, decode_key,
    decode_common_range, NodeType, set_position,
    set_next_key,  set_value, add_prefix,
    remove_prefix, equal_keys, NONE_ROOT
)


class Trie(BaseTrie):
    types = NodeType

    def __init__(self, root, db=None):
        self.db = db
        self.root = root
        self.cache = {}
        if self.root == NONE_ROOT:
            self.cache[self.root] = self.serialize(self.types.none)

    def serialize(self, value) -> bytes:
        return dumps(value)

    def deserialize(self, value) -> str:
        return loads(value)

    def put(self, key: str, value):
        key = hex_to_nibbles(key)
        node = self._get_node(self.root)
        next_node = self.add(node, key, value)
        return self._set_root(next_node)

    def _set_root(self, node):
        raw_node = self.serialize(node)
        key = sha3_hex(raw_node)
        self.cache[key] = raw_node
        self.root = key
        return key

    def _set_node(self, node):
        raw_node = self.serialize(node)
        key = sha3_hex(raw_node)
        self.cache[key] = raw_node
        return key

    def add(self, node, key, value):
        node_type = decode_type(node)
        if node_type == self.types.none:
            return self.add_leaf(key, value)
        elif node_type in (self.types.extension, self.types.leaf):
            return self.add_encode_node(node, key, value)
        elif node_type == self.types.branch:
            return self.add_branch(node, key, value)
        return node

    def add_leaf(self, key, value):
        return [add_prefix(key, self.types.leaf), value]

    def add_branch(self, node, key, value):
        if key:
            memorize = set_position(key)
            child_node = self._get_node(node[memorize])
            next_node = self.add(child_node, set_next_key(key), value)
            node[memorize] = self._set_node(next_node)
        elif not key:
            node[-1] = value
        return node

    def add_encode_node(self, node, key, value):
        node_type, prefix, parent_key, current_key = decode_key(node, key)

        if not parent_key and not current_key:
            if node_type == self.types.leaf:
                return [node[0], value]
            else:
                child_node = self._get_node(set_value(node))
                next_node = self.add(child_node, current_key, value)
        elif not parent_key:
            if node_type == self.types.extension:
                child_node = self._get_node(set_value(node))
                next_node = self.add(child_node, current_key, value)
            else:
                memorize = set_position(current_key)
                child_key = add_prefix(set_next_key(current_key), self.types.leaf)
                child_node = [child_key, value]

                next_node = [''] * 17
                next_node[-1] = set_value(node)
                next_node[memorize] = self._set_node(child_node)
        else:
            next_node = self.add_new_branch(node_type, node, parent_key, current_key, value)

        if prefix:
            return [add_prefix(prefix, self.types.extension), self._set_node(next_node)]
        else:
            return next_node

    def add_new_branch(self, node_type, node, parent_key, current_key, value):
        next_node = [''] * 17

        if len(parent_key) == 1 and node_type == self.types.extension:
            memorize = set_position(parent_key)
            next_node[memorize] = set_value(node)

        elif node_type == self.types.extension:
            memorize = set_position(parent_key)
            _next_node = [
                add_prefix(set_next_key(parent_key), self.types.extension),
                set_value(node)
            ]
            next_node[memorize] = self._set_node(_next_node)

        elif node_type == self.types.leaf:
            memorize = set_position(parent_key)
            _next_node = [
                add_prefix(set_next_key(parent_key), self.types.leaf),
                set_value(node)
            ]
            next_node[memorize] = self._set_node(_next_node)

        if current_key:
            memorize = set_position(current_key)
            _next_node = [
                add_prefix(set_next_key(current_key), self.types.leaf),
                value
            ]
            next_node[memorize] = self._set_node(_next_node)
        else:
            next_node[-1] = value
        return next_node

    def _get_node(self, key):
        if key == '':
            return self.types.none
        if key in self.cache:
            return self.deserialize(self.cache[key])
        try:
            raw_node = self.db.get(key)
            node = self.deserialize(raw_node)   # db.get
            self.cache[key] = raw_node
        except KeyError:
            node = self.types.none
        return node

    def get(self, key):
        key = hex_to_nibbles(key)
        node = self._get_node(self.root)
        value = self.get_decode_node(node, key)
        if value == self.types.none:
            raise KeyError(str(key))
        return value

    def get_decode_node(self, node, key):
        if not key:
            return node[-1]

        node_type = decode_type(node)
        if node_type == self.types.none:
            return self.types.none
        if node_type == self.types.branch:
            return self._decode_branch(node, key)
        elif node_type in (self.types.extension, self.types.leaf):
            return self._decode_leaf_and_extension(node_type, node, key)

    def _decode_branch(self, node, key):
        if not key:
            return self.types.none
        else:
            child_node = self._get_node(node[set_position(key)])
            return self.get_decode_node(child_node, set_next_key(key))

    def _decode_leaf_and_extension(self, node_type, node, key):
        parent_key = remove_prefix(set_position(node), node_type)
        if node_type == self.types.extension:
            if equal_keys(parent_key, key):
                common = decode_common_range(parent_key, key)
                child_node = self._get_node(set_value(node))
                return self.get_decode_node(child_node, key[common:])
            else:
                return self.types.none

        elif node_type == self.types.leaf:
            return node[1] if key == parent_key else 'none'

        else:
            raise TypeError('type unexpected')

    def search_all(self) -> list:
        node = self._get_node(self.root)
        all_state = []
        self.search_branch(node, all_state)
        return all_state

    def search_node(self, node, node_type, all_state):
        if node_type == self.types.leaf:
            if isinstance(node[1], dict):
                all_state.append(node[1])
        elif node_type == self.types.branch:
            self.search_branch(node, all_state)
        elif node_type == self.types.extension:
            self.search_extension(node, all_state)
        else:
            TypeError("unexpected type: {}".format(node))

    def search_branch(self, node, all_state):
        for key in node:
            if not key:
                continue
            inner_node = self._get_node(key)
            node_type = decode_type(inner_node)
            self.search_node(inner_node, node_type, all_state)

    def search_extension(self, node, all_state):
        inner_node = self._get_node(node[1])
        node_type = decode_type(inner_node)
        self.search_node(inner_node, node_type, all_state)

    def remove(self, key):
        pass

    def commit(self):
        if self.db is None:
            raise ValueError("is not state")
        with self.db.write_batch() as batch:
            for k, v in self.cache.items():
                batch.put(k, v)
        return self.root

    def clear(self):
        self.cache.clear()

