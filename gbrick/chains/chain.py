
import time
import asyncio

from utils.singleton import singleton
from utils.logger import getLogger
from utils.exceptions import ValidationError, FinalizeError
from utils.crypto.ec import verify

from utils.config import MainConstant as Constant
from utils.trie.prepare import make_hash_root

from gbrick.chains.base import BaseChain
from gbrick.wagon.wagon import Wagon
from gbrick.wagon.state import State
from gbrick.types.prepare import prepare_block, prepare_header

from utils.util import (
    uptime
)

from gbrick.validation import (
    validate_header_slots, validate_block_slots
)


from gbrick.types.base import (
    BaseHeader, BaseBlock
)


@singleton
class Chain(BaseChain):
    __slots__ = ('_signer', '_db_context', '_node_base', '_loop', '_start_at')
    _wagon = Wagon
    _state = State
    _version = 1

    """management chain, wagon
    """

    def __init__(self, **kwargs):
        """
            :param kwargs:  db_context: db context class
                            signer: node signer class
                            node_base: node address
                            start_at: node start time
                            loop: event loop
        """
        for k, v in kwargs.items():
            var_name = '_{}'.format(k)
            setattr(self, var_name, v)

    @property
    def height(self):
        return self._db_context.chain.get_current_height()

    @property
    def uptime(self):
        return uptime(self._start_at)

    @property
    def nodebase(self):
        return self._node_base

    @property
    def chain_id(self):
        return self._db_context.chain.get_chain_id()

    @property
    def logger(self):
        if self._logger is None:
            self._logger = getLogger('chain')
        return self._logger

    @property
    def version(self):
        return self._version

    @property
    def is_validator(self):
        validator_set = self._db_context.state.get_validator_id()
        return self.nodebase in validator_set

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def block_from_genesis(self):
        constant = Constant
        if constant.block_hash in self._db_context.chain:
            return False

        genesis_header = prepare_header(hash_prev_block=b'',
                                        num_height=constant.height,
                                        address_creator=b'',
                                        num_version=constant.constant_ver,
                                        chain_id=constant.constant_id)

        genesis_block = prepare_block(header=genesis_header,
                                      list_vote=[],
                                      list_transactions=[])

        wagon = self.prepare_wagon(None)
        genesis_block = wagon.genesis_declare(genesis_block, constant)

        genesis_block.header.hash_block = genesis_block.hash
        self._link_block(genesis_block, wagon, self._start_at)
        return True

    def _from_genesis(self, block):
        if block.height != 0:
            raise ValidationError(
                "genesis block height {}"
                "current block height {}".format(
                    0, block.height
                )
            )
        if block.hash != Constant.block_hash:
            raise ValidationError(
                "genesis hash {}"
                "current hash {}".format(
                    Constant.block_hash, block.hash
                )
            )
        if block.header.hash_state_root != Constant.state_root:
            raise ValidationError(
                "genesis state root: {} "
                "current state root: {}".format(
                    Constant.state_root, block.header.hash_state_root
                )
            )

        self._db_context.chain.commit(block)

    def has_block(self, b_hash):
        return b_hash in self.chain_db

    def has_transaction(self, tx_hash):
        return self._db_context.chain.has_transaction(tx_hash)

    def has_validator(self, validator_id):
        return validator_id in self.get_validator_id_set()

    def get_balance(self, address: bytes):
        return self._db_context.state.get_balance(address)

    def get_nonce(self, addres: bytes):
        return self._db_context.state.get_nonce(addres)

    def get_account(self, address: bytes):
        return self._db_context.state.get_account(address)

    def get_delegated(self, address: bytes):
        return self._db_context.state.get_delegated(address)

    def get_transaction(self, tx_hash):
        return self._db_context.chain.get_transaction_from_lookup(tx_hash)

    def get_receipt(self, tx_hash):
        return self._db_context.chain.get_receipt(tx_hash)

    def get_block_from_hash(self, b_hash) -> BaseBlock:
        return self._db_context.chain.get_block_from_hash(b_hash)

    def get_header_from_hash(self, block_hash) -> BaseHeader:
        return self._db_context.chain.get_header_from_hash(block_hash)

    def get_block_from_height(self, height) -> BaseBlock:
        return self._db_context.chain.get_block_from_height(height)

    def get_header_from_height(self, height) -> BaseHeader:
        return self._db_context.chain.get_header_from_height(height)

    def get_validator_id_set(self):
        return self._db_context.state.get_validator_id()

    def get_validator_set(self):
        # return self._db_context.state.get_const_validator()
        return self._db_context.state.get_const_validator_list()

    def get_validator_count(self):
        return self._db_context.state.get_validator_count()

    def get_wagon(self):
        header = self.get_header_from_height(self.height)
        return self.prepare_wagon(header)

    def prepare_wagon(self, header):
        return self._wagon(self._db_context, header)

    def make_signature(self, hash_data):
        return self._signer(hash_data)

    async def validate_header(self, permit_header: BaseHeader, block: BaseBlock):
        header = block.header
        if self.chain_id != header.chain_id:
            raise ValidationError(
                "main chain id: {} "
                "current header chain id: {}".format(
                    self.chain_id, header.chain_id
                )
            )
        validate_header_slots(header.to_dict())
        await verify(header.hash,
                     header.byte_signature,
                     header.address_creator)

        if permit_header.num_height + 1 != header.num_height:
            raise FinalizeError(
                "permit header height: {} "
                "current header height: {}".format(
                    permit_header.num_height, header.num_height
                )
            )

        if permit_header.hash != block.previous:
            raise FinalizeError(
                "previous hash: {}, "
                "current block previous hash: {} ".format(
                    permit_header.hash, block.previous
                )
            )

        if permit_header.timestamp >= header.timestamp:
            raise ValidationError(
                "permit header time: {} "
                "current header time: {}".format(
                    permit_header.timestamp, header.timestamp
                )
            )

        tx_root = make_hash_root(block.list_transactions).root
        if tx_root != block.header.hash_transaction_root:
            raise ValidationError(
                "current header tx root: {} "
                "digest tx root: {}".format(
                    block.header.hash_transaction_root, tx_root
                )
            )

        vt_root = make_hash_root(block.list_vote).root
        if vt_root != block.header.hash_vote_root:
            raise ValidationError(
                "vote root error"
            )

    async def validate_vote(self, header: BaseHeader, vt_list):
        for vote in vt_list:
            await verify(vote.hash_vote,
                         vote.byte_signature,
                         vote.address_creator)

            if vote.hash_vote != vote.hash:
                raise ValidationError(
                    "saved vote hash: {} "
                    "digest vote hash: {}".format(
                        vote.hash_vote, vote.hash
                    )
                )
            if header.num_height != vote.num_block_height:
                raise ValidationError(
                    "current header height: {} "
                    "vote height: {}".format(
                        header.num_height, vote.num_block_height
                    )
                )

    async def validate_block(self, block: BaseBlock) -> None:
        validate_block_slots(block.to_dict())
        permit_block = self.get_block_from_hash(block.previous)
        await self.validate_header(permit_block.header, block)
        await self.validate_vote(block.header, block.list_vote)

        # prev reps list hash -> current header rep_hash

    def prepare_candidate_from_header(self, header: BaseHeader) -> BaseBlock:
        header = prepare_header(num_version=self.version,
                                chain_id=self.chain_id,
                                hash_prev_block=header.hash,
                                num_height=header.num_height+1,
                                address_creator=self.nodebase)

        block = prepare_block(header=header,
                              list_transactions=[],
                              list_vote=[])
        return block.copy()

    async def make_finalize_from_confirm(self, confirm_block: BaseBlock, vt_list) -> BaseBlock:
        tx_trie = make_hash_root(confirm_block.list_transactions)

        permit_header = self.get_header_from_hash(confirm_block.previous)

        wagon = self.prepare_wagon(permit_header)

        if confirm_block.header.hash_transaction_root != tx_trie.root:
            raise ValidationError("tx root not matched")

        confirm_block.list_vote.extend(vt_list)

        vt_trie = make_hash_root(vt_list)

        confirm_block.header.hash_vote_root = vt_trie.root

        block = await wagon.execute_transactions(self.version, confirm_block)

        block.header.hash_vote_root = vt_trie.root

        block.header.timestamp_finalize = time.time()

        signature = self.make_signature(block.hash)

        wagon.clear()

        return block.copy(header=block.header.copy(hash_block=block.hash,
                                                   byte_signature=signature),
                          list_vote=vt_list)

    def validate_chains(self, block: BaseBlock):
        pass

    async def finalize(self, block: BaseBlock) -> None:
        await self.validate_block(block)
        wagon = self.get_wagon()
        start_at = time.time()
        block = await wagon.execute_transactions(self.version, block)

        if block.header.hash_block != block.hash:
            raise ValidationError(
                "final-block hash error "
                "block-hash: {}, current-hash: {}".format(
                    block.header.hash_block, block.hash
                ))
        # fully executed transaction.
        self._link_block(block, wagon, start_at)

    def _link_block(self, block, wagon, start_at) -> None:
        if block.height == 0 and block.previous == b'':
            self._from_genesis(block)
            return None
        permit_header = self.get_header_from_hash(block.previous)
        wagon.finalize(block)
        e_time = time.time() - start_at
        self.logger.debug(
            "new link {} -> {}: {}, "
            "execute: {}, elapsed time: {}".format(
                permit_header.num_height, block.height,
                block.hash, len(block.list_transactions),
                round(e_time, 6)
            )
        )



