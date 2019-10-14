
import json

from utils.crypto.ec import verify
from utils.trie.prepare import make_hash_root
from utils.exceptions import ValidationError
from event.base import BaseEventContext
from utils.config import (
    O_COIN_TYPE,
    CONTRACT_TYPE
)

from gbrick.types.config import (
    HEADER_DICT, TX_DICT, BLOCK_DICT,
    VT_DICT, ACCOUNT_DICT, RECEIPT_DICT
)

from gbrick.types.base import (
    BaseHeader,
    BaseBlock,
    BaseTransaction,
    BaseVote
)

from utils.config import ADDRESS_SIZE


def validate_header_slots(header_dict: dict) -> None:
    unknown_slots = set(header_dict.keys()).difference(HEADER_DICT)
    if unknown_slots:
        raise ValidationError(
            "header be used with slots {}"
            " provide unknown slots {}".format(
                HEADER_DICT, unknown_slots
            )
        )


def validate_block_slots(block_dict: dict) -> None:
    unknown_slots = set(block_dict.keys()).difference(BLOCK_DICT)
    if unknown_slots:
        raise ValidationError(
            "block be used with slots {}"
            " provide unknown slots {}".format(
                BLOCK_DICT, unknown_slots
            )

        )


def validate_transaction_slots(tx_dict: dict) -> None:
    unknown_slots = set(tx_dict.keys()).difference(TX_DICT)
    if unknown_slots:
        raise ValidationError(
            "transaction be used with slots {}"
            " provide unknown slots {}".format(
                TX_DICT, unknown_slots
            )
        )


def validate_vote_slots(vt_dict: dict) -> None:
    unknown_slots = set(vt_dict.keys()).difference(VT_DICT)
    if unknown_slots:
        raise ValidationError(
            "vote be used with slots {}"
            " provide unknown slots {}".format(
                VT_DICT, unknown_slots
            )
        )


def validate_receipt_slots(rct_dict: dict) -> None:
    unknown_slots = set(rct_dict.keys()).difference(RECEIPT_DICT)
    if unknown_slots:
        raise ValidationError(
            "receipt be used with slots {}"
            " provide unknown slots {}".format(
                RECEIPT_DICT, unknown_slots
            )
        )


def validate_account_slots(account_dict: dict) -> None:
    unknown_slots = set(account_dict.keys()).difference(ACCOUNT_DICT)
    if unknown_slots:
        raise ValidationError(
            "account be used with slots {}"
            " provide unknown slots {}".format(
                ACCOUNT_DICT, unknown_slots
            )
        )


def validate_payable(transaction, balance):
    amount_paid = transaction.amount_value + transaction.amount_fee
    balance_left = balance - amount_paid

    if balance_left < 0:
        raise ValidationError(
            'payment refused, amount total paid: {}, account balance: {}'.format(
                amount_paid, balance))
    else:
        return True


def validate_address(node_base) -> None:
    if not isinstance(node_base, bytes):
        raise ValidationError("address is not bytes, {}".format(type(node_base)))

    if not node_base.startswith((O_COIN_TYPE, CONTRACT_TYPE)):
        raise ValidationError("address not allowed {}".format(node_base))

    if len(node_base) != ADDRESS_SIZE:
        raise ValidationError(
            "address specific length: {}, current length: {}, current address: {}".format(
                ADDRESS_SIZE, len(node_base), node_base
            )
        )


def validate_contract(node_base) -> None:
    if not isinstance(node_base, bytes):
        raise ValidationError("address is not bytes, {}".format(type(node_base)))

    if not node_base.startswith(b'gBc'):
        raise ValidationError("address not allowed {}".format(node_base))

    if len(node_base) != ADDRESS_SIZE:
        raise ValidationError(
            "address specific length: {}, current length: {}, current address: {}".format(
                ADDRESS_SIZE, len(node_base), node_base
            )
        )


def validate_has_transactions(transactions, chain):
    auth = []
    for tx in transactions:
        if not chain.has_transaction(tx.hash):
            auth.append(tx.copy())
    if len(auth) < 1:
        raise ValidationError("execute set is empty.")
    return auth


def validate_validator_set(validator_set, chain) -> None:
    for validator in validator_set:
        if not chain.has_validator(validator):
            raise ValidationError("validator set: {}, "
                                  "{} not in validator set."
                                  "".format(chain.get_validator_id_set(), validator))


def validate_context_height(header: BaseHeader, context: BaseEventContext) -> None:
    if header.num_height + 1 != context.height:
        raise ValidationError(
            "permit header height: {} "
            "current event context height: {}".format(
                header.num_height, context.height
            )
        )


def validate_code(code):
    if not code:
        return None
    if not isinstance(code, bytes):
        code = code.encode()
    return code


def validate_json(value) -> str:
    if not isinstance(value, dict):
        value = json.loads(value)
    return value


def validate_nonce(context_nonce, account_nonce) -> None:
    if context_nonce != account_nonce:
        raise ValidationError(
            "current account nonce: {}"
            "execute context nonce: {}".format(
                account_nonce,
                context_nonce + 1
            )
        )


async def validate_transaction(tx: BaseTransaction) -> None:
    # if not isinstance(tx.hash_transaction, bytes):
    #     raise ValueError('tx hash is not bytes')
    if tx.hash_transaction != tx.hash:
        raise ValidationError(
            "transaction hash: {} "
            "current transaction hash: {}".format(
                tx.hash, tx.hash_transaction
            )
        )
    await verify(tx.hash,
                 tx.byte_signature,
                 tx.address_sender)


async def validate_candidate(block: BaseBlock) -> None:
    if block.pre_hash != block.header.hash_candidate_block:
        raise ValidationError(
            "candidate hash: {} "
            "current candidate hash: {}".format(
                block.pre_hash, block.header.hash_candidate_block
            )
        )
    await verify(block.pre_hash,
                 block.header.byte_signature,
                 block.header.address_creator)

    trie = make_hash_root(block.list_transactions)
    if block.header.hash_transaction_root != trie.root:
        raise ValidationError(
            "block tx root: {}"
            "current block tx root: {}".format(
               trie.root, block.header.hash_transaction_root
            )
        )


async def validate_vote(vote: BaseVote) -> None:
    if vote.hash != vote.hash_vote:
        raise ValidationError(
            "vote hash: {} "
            "current vote hash: {}".format(
                vote.hash, vote.hash_vote
            )
        )
    await verify(vote.hash,
                 vote.byte_signature,
                 vote.address_creator)


async def validate_finalize(block: BaseBlock) -> None:
    if block.hash != block.header.hash_block:
        raise ValidationError(
            "finalize hash: {} "
            "current finalize hash: {}".format(
                block.hash, block.header.hash_block
            )
        )
    await verify(block.hash,
                 block.header.byte_signature,
                 block.header.address_creator)


