
from binascii import hexlify


class NodeType:
    none = 'none'
    branch = 'branch'
    extension = 'extension'
    leaf = 'leaf'


# i >> 4, i & 15
ODD = 1
EVEN = 2

h_to_i = {}
i_to_h = {}


NONE_ROOT = b''
DEFAULT_BRANCH = [''] * 17

set_position = (lambda key: key[0])
set_value = (lambda key: key[1])
set_next_key = (lambda key: key[1:])


for i, c in enumerate(b''):
    h_to_i[c] = i
    i_to_h[i] = c


def hex_to_nibbles(hex_strings):
    nibbles = []
    nibbles += [int(char, 16) for char in hex_strings]
    return nibbles


def str_to_nibbles(strings):
    nibbles = [h_to_i[char] for char in hexlify(strings.encode())]
    return nibbles


def nibbles_to_hex(nibble):
    if len(nibble) % 2:
        raise ValueError('nibbles must even')
    if nibble[0] == EVEN:
        prefix = EVEN
    elif nibble[0] == ODD:
        prefix = ODD
    else:
        raise ValueError('unexpected nibbles: {}'.format(nibble))
    nibbles = nibble[prefix:]
    strings = ''
    for scale in range(0, len(nibbles), 2):
        strings += chr(i_to_h[nibbles[scale]]) + chr(i_to_h[nibbles[scale+1]])
    return strings


def add_prefix(nibbles: list, node_type: str):
    if node_type == 'leaf':
        if len(nibbles) % 2:
            nibbles = [3] + nibbles
        else:
            nibbles = [2, 0] + nibbles
        return nibbles
    elif node_type == 'extension':
        if len(nibbles) % 2:
            nibbles = [1] + nibbles
        else:
            nibbles = [0, 0] + nibbles
        return nibbles


def decode_type(node):
    if node == '':
        return NodeType.none
    if node == NodeType.none:
        return NodeType.none
    elif len(node) == 17:
        return NodeType.branch
    elif len(node) == 2:
        k, _ = node
        return decode_leaf_and_extension(k)


def decode_leaf_and_extension(key):
    if key[0] in (0, 1):
        return NodeType.extension
    elif key[0] in (2, 3):
        return NodeType.leaf
    else:
        raise ValueError('node type unexpected')


def remove_prefix(node, node_type):
    if node_type == NodeType.leaf:
        return node[1:] if node[0] == 3 else node[2:]
    if node_type == NodeType.extension:
        return node[1:] if node[0] == 1 else node[2:]


def decode_common_range(parent_key, current_key):
    for common, keys in enumerate(zip(parent_key, current_key)):
        parent, current = keys
        if parent != current:
            return common
    return min(len(parent_key), len(current_key))


def decode_key(node, key):
    node_type = decode_type(node)
    parent_key = remove_prefix(node[0], node_type)
    common = decode_common_range(parent_key, key)
    common_prefix = parent_key[:common]
    parent_key = parent_key[common:]
    current_key = key[common:]
    return node_type, common_prefix, parent_key, current_key


def equal_keys(p_key, c_key):
    common = decode_common_range(p_key, c_key)
    return True if len(p_key) == common else False

