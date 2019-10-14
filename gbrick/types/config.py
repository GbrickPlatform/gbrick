
HEADER_DICT = [
        'prev_hash',
        'height',
        'tx_root_hash',
        'creator',
        'timestamp',
        'version',
        'chain_id',
        'candidate_block_hash',
        'vote_root_hash',
        'receipt_root',
        'state_root',
        'finalized_timestamp',
        # 'finalized_time',
        'block_hash',
        'signature'
    ]

BLOCK_DICT = [
        'header',
        'transaction_list',
        'vote_list',
        'extra'
    ]

TX_DICT = [
        'version',
        'type',
        'from',
        'to',
        'value',
        'fee',
        'message',
        'timestamp',
        'tx_hash',
        'signature'
    ]

VT_DICT = [
        'version',
        'block_height',
        'candidate_block_hash',
        'creator',
        'vote_hash',
        'signature'
]

RECEIPT_DICT = [
        'tx_hash',
        'height',
        'fee_limit',
        'paid_fee',
        'created_address',
        'status',
        'message',
        'error_message'
]

ACCOUNT_DICT = [
        'address',
        'type',
        'nonce',
        'balance',
        'delegated',
        'delegated_balance',
        'node_id',
        'node_signature',
        'state',
        'code'
]

STAKE_DICT = [
        'from',
        'to',
        'stake'
]

REP_DICT = [
        'node_id',
        'account',
        'delegated'
]

EOA = 'eoa'
PENDING = 'pending'


