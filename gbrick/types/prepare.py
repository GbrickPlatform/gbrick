
from typing import List
from gbrick.types.config import EOA

from gbrick.types import (
    Transaction, Receipt, BlockHeader,
    Block, Account, Rep, Vote
)

# prepare data creation.


def prepare_header(hash_transaction_root: bytes = b'',
                   hash_vote_root: bytes = b'',
                   hash_receipt_root: bytes = b'',
                   hash_state_root: bytes = b'',
                   timestamp=0,
                   timestamp_finalize=0,
                   hash_candidate_block: bytes = b'',
                   block_hash: bytes = b'',
                   signature: bytes = b'',
                   **kwargs) -> BlockHeader:

    return BlockHeader(hash_transaction_root=hash_transaction_root,
                       timestamp=timestamp,
                       hash_candidate_block=hash_candidate_block,
                       hash_vote_root=hash_vote_root,
                       hash_receipt_root=hash_receipt_root,
                       hash_state_root=hash_state_root,
                       timestamp_finalize=timestamp_finalize,
                       hash_block=block_hash,
                       byte_signature=signature,
                       **kwargs)


def prepare_block(header: BlockHeader,
                  list_transactions: List[Transaction] = None,
                  list_vote: List[Vote] = None) -> Block:
    if list_transactions is None:
        list_transactions = []
    if list_vote is None:
        list_vote = []
    return Block(header=header,
                 list_transactions=list_transactions,
                 list_vote=list_vote,
                 extra_data={})


def prepare_transaction(tx_hash: bytes = b'',
                        signature: bytes = b'',
                        **kwargs) -> Transaction:
    return Transaction(hash_transaction=tx_hash,
                       byte_signature=signature,
                       **kwargs)


def prepare_receipt(**kwargs) -> Receipt:
    return Receipt(**kwargs)


def prepare_vote(vote_hash: bytes = b'',
                 signature: bytes = b'',
                 **kwargs) -> Vote:
    return Vote(hash_vote=vote_hash,
                byte_signature=signature,
                **kwargs)


def prepare_account(balance: int = 0,
                    nonce: int = 0,
                    type=EOA,
                    delegated: list = None,
                    delegated_balance: int = 0,
                    node_id: bytes = b'',
                    node_signature: bytes = b'',
                    state: dict = None,
                    code: bytes = b'',
                    **kwargs) -> Account:

    if state is None:
        state = {}
    if delegated is None:
        delegated = []
    if nonce is None:
        nonce = 0

    return Account(type=type,
                   nonce=nonce,
                   balance=balance,
                   delegated=delegated,
                   delegated_stake_balance=delegated_balance,
                   node_id=node_id,
                   node_signature=node_signature,
                   state=state,
                   code=code,
                   **kwargs)


def prepare_rep(node_id, account, delegate) -> Rep:
    return Rep(
        node_id=node_id,
        address_account=account,
        delegated_balance=delegate
    )


