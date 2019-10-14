
from pickle import dumps, loads
from gbrick.db.base import BaseChainDB

from utils.config import Lookup
from utils.trie.prepare import prepare_trie, make_hash_root

from gbrick.types.base import (
    BaseBlock, BaseHeader, BaseTransaction,
    BaseVote
)

from gbrick.types.deserializer import (
    deserialize_block, deserialize_header

)

from utils.util import (
    int_to_bytes32, bytes_to_int, get_trie_key
)

(
    BLOCK_CONTEXT,
    HEADER_CONTEXT
) = tuple(range(2))


class ChainDB(BaseChainDB):

    def serialize(self, obj):
        return dumps(obj.to_dict())

    def deserialize(self, raw_dict, context=BLOCK_CONTEXT):
        return self._deserialize(loads(raw_dict), context)

    def _deserialize(self, dict_obj, context):
        if context == HEADER_CONTEXT:
            return self._deserialize_header(dict_obj)
        elif context == BLOCK_CONTEXT:
            return self._deserialize_block(dict_obj)

    def _deserialize_block(self, dict_obj) -> BaseBlock:
        return deserialize_block(dict_obj)

    def _deserialize_header(self, dict_obj) -> BaseHeader:
        return deserialize_header(dict_obj)

    def get_chain_id(self):
        header = self.get_header_from_height(0)
        return header.chain_id

    def get_block_hash(self, height):
        header = self.get_header_from_height(height)
        return header.hash_block

    def get_block_from_height(self, height) -> BaseBlock:
        block_hash = self.get_block_hash(height)
        raw_block = self.db.get(block_hash)
        return self.deserialize(raw_block)

    def get_header_from_height(self, height) -> BaseHeader:
        raw_header = self.db.get(int_to_bytes32(height))
        return self.deserialize(raw_header, HEADER_CONTEXT)

    def get_block_from_hash(self, block_hash) -> BaseBlock:
        raw_block = self.db.get(block_hash)
        return self.deserialize(raw_block)

    def get_header_from_hash(self, block_hash) -> BaseHeader:
        block = self.get_block_from_hash(block_hash)
        return block.header

    def get_current_height(self):
        return bytes_to_int(self.db.get(Lookup.top_header()))

    def has_transaction(self, tx_hash):
        lookup = Lookup.transaction(tx_hash)
        return lookup in self.db

    def _set_transaction_from_lookup(self, height, seek_index, transaction):
        lookup_key = Lookup.transaction(transaction.hash)
        leaf_key = dumps((height, seek_index))
        self.db.put(lookup_key, leaf_key)

    def get_transaction_from_lookup(self, tx_hash) -> BaseTransaction:
        lookup = Lookup.transaction(tx_hash)
        if lookup in self.db:
            height, seek_index = loads(self.db.get(lookup))
            header = self.get_header_from_height(height)
            tx_root = header.hash_transaction_root
            trie = prepare_trie(tx_root, self.db)
            trie_key = get_trie_key(int_to_bytes32(seek_index))
            tx = trie.get(trie_key)
            return tx

    def _set_vote_from_lookup(self, height, seek_index, vote):
        lookup_key = Lookup.vote(vote.hash)
        leaf_key = dumps((height, seek_index))
        self.db.put(lookup_key, leaf_key)

    def get_vote_from_lookup(self, vote_hash) -> BaseVote:
        lookup = Lookup.vote(vote_hash)
        if lookup in self.db:
            height, seek_index = loads(self.db.get(lookup))
            header = self.get_header_from_height(height)
            vote_root = header.hash_vote_root
            trie = prepare_trie(vote_root, self.db)
            trie_key = get_trie_key(int_to_bytes32(seek_index))
            vote = trie.get(trie_key)
            return vote

    def set_trie(self, trie):
        with self.db.write_batch() as batch:
            for k, v in trie.cache.items():
                batch.put(k, v)
        trie.clear()

    def get_receipt(self, tx_hash):
        lookup = Lookup.transaction(tx_hash)
        if lookup in self.db:
            height, seek_index = loads(self.db.get(lookup))
            header = self.get_header_from_height(height)
            receipt_root = header.hash_receipt_root
            trie = prepare_trie(receipt_root, self.db)
            trie_key = get_trie_key(int_to_bytes32(seek_index))
            receipt = trie.get(trie_key)
            return receipt

    def commit(self, block: BaseBlock):
        self.db.put(Lookup.top_header(), int_to_bytes32(block.header.num_height))
        # not padding.
        self.db.put(int_to_bytes32(block.header.num_height), self.serialize(block.header))
        self.db.put(block.hash, self.serialize(block))
        # Lookup(height, index) ->
        # block tx root -> Trie.root = root hash -> Trie.get(index-key)
        for index, tx in enumerate(block.list_transactions):
            self._set_transaction_from_lookup(
                block.height, index, tx
            )

        for index, vote in enumerate(block.list_vote):
            self._set_vote_from_lookup(
                block.height, index, vote
            )

    def __contains__(self, block_hash):
        return self.db.exists(block_hash)

