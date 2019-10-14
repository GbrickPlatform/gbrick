
from utils.util import extract_values

from gbrick.types.config import (
    BLOCK_DICT,
    HEADER_DICT,
    TX_DICT,
    VT_DICT,
    ACCOUNT_DICT,
    RECEIPT_DICT
)

from gbrick.types.base import (
    BaseHeader,
    BaseBlock,
    BaseTransaction,
    BaseVote,
    BaseAccount,
    BaseReceipt
)

from gbrick.types.prepare import (
    prepare_header,
    prepare_block,
    prepare_transaction,
    prepare_vote,
    prepare_account,
    prepare_receipt
)

from gbrick.validation import (
    validate_header_slots,
    validate_block_slots,
    validate_transaction_slots,
    validate_vote_slots,
    validate_account_slots,
    validate_receipt_slots
)


def deserialize_header(dict_obj) -> BaseHeader:
    validate_header_slots(dict_obj)
    ex_header = extract_values(dict_obj, HEADER_DICT)
    return prepare_header(hash_prev_block=ex_header.prev_hash.encode(),
                          num_height=int(ex_header.height),
                          hash_transaction_root=ex_header.tx_root_hash.encode(),
                          address_creator=ex_header.creator.encode(),
                          timestamp=ex_header.timestamp,
                          num_version=int(ex_header.version),
                          chain_id=int(ex_header.chain_id),
                          hash_candidate_block=ex_header.candidate_block_hash.encode(),
                          hash_vote_root=ex_header.vote_root_hash.encode(),
                          hash_receipt_root=ex_header.receipt_root.encode(),
                          hash_state_root=ex_header.state_root.encode(),
                          timestamp_finalize=ex_header.finalized_timestamp,
                          block_hash=ex_header.block_hash.encode(),
                          signature=ex_header.signature.encode())


def deserialize_block(dict_obj) -> BaseBlock:
    validate_block_slots(dict_obj)
    ex_block = extract_values(dict_obj, BLOCK_DICT)
    header = deserialize_header(ex_block.header)

    transaction_list = [
        deserialize_transaction(obj)
        for obj in ex_block.transaction_list
    ]

    vote_list = [
        deserialize_vote(obj)
        for obj in ex_block.vote_list
    ]

    return prepare_block(header=header,
                         list_transactions=transaction_list,
                         list_vote=vote_list)


def deserialize_transaction(dict_obj) -> BaseTransaction:
    validate_transaction_slots(dict_obj)

    ex_transaction = extract_values(dict_obj, TX_DICT)

    return prepare_transaction(num_version=int(ex_transaction.version),
                               type_transaction=ex_transaction.type,
                               address_sender=getattr(ex_transaction, 'from').encode(),
                               address_recipient=ex_transaction.to.encode(),
                               amount_value=int(ex_transaction.value),
                               amount_fee=int(ex_transaction.fee),
                               message=ex_transaction.message,
                               timestamp=float(ex_transaction.timestamp),
                               tx_hash=ex_transaction.tx_hash.encode(),
                               signature=ex_transaction.signature.encode())


def deserialize_vote(dict_obj) -> BaseVote:
    validate_vote_slots(dict_obj)
    ex_vote = extract_values(dict_obj, VT_DICT)
    return prepare_vote(num_version=int(ex_vote.version),
                        num_block_height=int(ex_vote.block_height),
                        hash_candidate_block=ex_vote.candidate_block_hash.encode(),
                        address_creator=ex_vote.creator.encode(),
                        vote_hash=ex_vote.vote_hash.encode(),
                        signature=ex_vote.signature.encode())


def deserialize_account(dict_obj) -> BaseAccount:
    validate_account_slots(dict_obj)
    ex = extract_values(dict_obj, ACCOUNT_DICT)
    return prepare_account(address_account=ex.address.encode(),
                           nonce=ex.nonce,
                           balance=ex.balance,
                           delegated=ex.delegated,
                           delegated_balance=ex.delegated_balance,
                           type=ex.type,
                           node_id=ex.node_id,
                           node_signature=ex.node_signature,
                           state=ex.state)


def deserialize_receipt(dict_obj) -> BaseReceipt:
    validate_receipt_slots(dict_obj)
    ex = extract_values(dict_obj, RECEIPT_DICT)
    return prepare_receipt(hash_transaction=ex.tx_hash,
                           fee_limit=ex.fee_limit,
                           height=ex.height,
                           paid_fee=ex.paid_fee,
                           created_address=ex.created_address,
                           status=ex.status,
                           message=ex.message,
                           error_message=ex.error_message)


