
from abc import ABC, abstractmethod
from gbrick.types.serializer import Serializer
from gbrick.types.config import (
    HEADER_DICT, BLOCK_DICT, TX_DICT,
    RECEIPT_DICT, VT_DICT, ACCOUNT_DICT,
    REP_DICT
)


class BaseHeader(Serializer, ABC):
    dict_slots = HEADER_DICT
    __slots__ = (
        'hash_prev_block',
        'num_height',
        'hash_transaction_root',
        'address_creator',
        'timestamp',
        'num_version',
        'chain_id',
        'hash_candidate_block',
        'hash_vote_root',
        'hash_receipt_root',
        'hash_state_root',
        'timestamp_finalize',
        'hash_block',
        'byte_signature'
    )

    @property
    @abstractmethod
    def hash(self): raise NotImplementedError

    @property
    @abstractmethod
    def pre_hash(self): raise NotImplementedError


class BaseBlock(Serializer, ABC):
    dict_slots = BLOCK_DICT
    __slots__ = (
        'header',
        'list_transactions',
        'list_vote',
        'extra_data'
    )

    def __init__(self,
                 header: BaseHeader,
                 list_transactions,
                 list_vote,
                 extra_data):

        super().__init__(
            header,
            list_transactions,
            list_vote,
            extra_data
        )

    @property
    @abstractmethod
    def previous(self): raise NotImplementedError

    @property
    @abstractmethod
    def height(self): raise NotImplementedError

    @property
    @abstractmethod
    def creator(self): raise NotImplementedError

    @property
    @abstractmethod
    def hash(self): raise NotImplementedError

    @property
    @abstractmethod
    def pre_hash(self): raise NotImplementedError


class BaseTransaction(Serializer, ABC):
    dict_slots = TX_DICT
    __slots__ = (
        'num_version',
        'type_transaction',
        'address_sender',
        'address_recipient',
        'amount_value',
        'amount_fee',
        'message',
        'timestamp',
        'hash_transaction',
        'byte_signature'
    )

    @property
    @abstractmethod
    def hash(self): raise NotImplementedError


class BaseReceipt(Serializer, ABC):
    dict_slots = RECEIPT_DICT
    __slots__ = (
        'hash_transaction',
        'height',
        'fee_limit',
        'paid_fee',
        'created_address',
        'status',
        'message',
        'error_message'
    )

    @property
    @abstractmethod
    def hash(self): raise NotImplementedError


class BaseVote(Serializer, ABC):
    dict_slots = VT_DICT
    __slots__ = (
        'num_version',
        'num_block_height',
        'hash_candidate_block',
        'address_creator',
        'hash_vote',
        'byte_signature'
    )

    @property
    @abstractmethod
    def creator(self): raise NotImplementedError

    @property
    @abstractmethod
    def hash(self): raise NotImplementedError


class BaseAccount(Serializer, ABC):
    dict_slots = ACCOUNT_DICT
    __slots__ = (
        'address_account',
        'type',
        'nonce',
        'balance',
        'delegated',
        'delegated_stake_balance',
        'node_id',
        'node_signature',
        'state',
        'code'
    )

    @property
    @abstractmethod
    def base(self): raise NotImplementedError

    @property
    @abstractmethod
    def hash(self): raise NotImplementedError


class BaseRep(Serializer, ABC):
    dict_slots = REP_DICT
    __slots__ = (
        'node_id',
        'address_account',
        'delegated_balance'
    )

    @property
    @abstractmethod
    def hash(self): raise NotImplementedError

    # next up
    # tx -> type: 'register'
    # from: wallet account, to: rep node account
    # value : delegated value, wallet account -[delegated]-> rep node account
    # message = sign(sha3_hex(wallet_account), rep node account private key) [signature]
    # confirmation to rep node account,

