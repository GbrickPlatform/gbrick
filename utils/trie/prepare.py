
from utils.trie.util import NONE_ROOT
from utils.trie.trie import Trie
from utils.util import get_trie_key, int_to_bytes32


def prepare_single_trie() -> Trie:
    return Trie(root=NONE_ROOT)


def prepare_trie(state_root, db) -> Trie:
    return Trie(state_root, db)


def make_hash_root(list_obj):
    trie = prepare_single_trie()

    for seek_index, obj in enumerate(list_obj):

        trie_key = get_trie_key(int_to_bytes32(seek_index))

        trie.put(trie_key, obj.to_dict())
    return trie


