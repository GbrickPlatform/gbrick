
from abc import ABC, abstractmethod


class BaseChain(ABC):
    _version = None
    _logger = None
    _wagon = None

    """ base chain class
    
    """

    @property
    @abstractmethod
    def height(self):
        """
        :return: int, latest height get from chaindb
        """
        raise NotImplementedError('chain: method not implement')

    @property
    @abstractmethod
    def nodebase(self):
        """
        :return: bytes, node address
        """
        raise NotImplementedError('chain: method not implement')

    @property
    @abstractmethod
    def chain_id(self):
        """
        :return: int, from genesis
        """
        raise NotImplementedError('chain: method not implement')

    @property
    @abstractmethod
    def version(self):
        """
        :return: int, chain version
        """
        raise NotImplementedError('chain: method not implement')

    @property
    @abstractmethod
    def logger(self):
        """
        :return: logger, chain logger
        """
        raise NotImplementedError('chain: method not implement')

    @property
    @abstractmethod
    def is_validator(self):
        """
        :return: bool, node check
        """
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_event_loop(self):
        """
        :return: event loop
        """
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def block_from_genesis(self):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_validator_count(self):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def prepare_wagon(self, header):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def make_signature(self, hash_data):
        """ signing hash

        :param hash_data: bytes
        :return: bytes, signature
        """
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def validate_header(self, permit_header, block):
        """ validate header

        :param permit_header: header class
        :param block: block class
        :return: None

        :raise: ValidationError, FinalizeError
        """
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def validate_vote(self, header, vt_list):
        """ validate vote

        :param header: header class
        :param vt_list: list[vote, vote, ...]
        :return: None

        :raise: ValidationError
        """
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def validate_block(self, block):
        """ validate block

        :param block: block class
        :return: None

        :raise: ValidationError, FinalizeError
        """
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def validate_chains(self, block):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def finalize(self, block):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def has_block(self, block):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def has_transaction(self, tx_hash):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_transaction(self, tx_hash):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_receipt(self, tx_hash):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def has_validator(self, rep_id):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_validator_id_set(self):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_block_from_hash(self, block_hash):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_header_from_hash(self, block_hash):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_block_from_height(self, height):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_header_from_height(self, height):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_wagon(self):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def prepare_candidate_from_header(self, header):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def make_finalize_from_confirm(self, confirm_block, vt_list):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_balance(self, address):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_nonce(self, addres: bytes):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_account(self, address):
        raise NotImplementedError('chain: method not implement')

    @abstractmethod
    def get_delegated(self, address):
        raise NotImplementedError('chain: method not implement')


