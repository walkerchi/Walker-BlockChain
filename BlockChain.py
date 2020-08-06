
import hashlib
import json
import os
import pickle as pkl
from time import time
from uuid import uuid1
from collections import OrderedDict

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto import Random
import binascii

from textwrap import dedent
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests




# block = {
#     'index': 1,
#     'timestamp': 1506057125.900785,
#     'transactions': [
#         {
#             data{'sender_address': "8527147fe1f5426f9dd545de4b27ee00",
#                'recipient_address': "a77f5cdfa2934df3954a5c7c7da5df1f",
#                'value': 5
#                   }
#             'signature': ....
#         }
#     ],
#     'proof': 324984774000,
#     'previous_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
# }


# Transaction{
#     sender_address
#     sender_private_key
#     recipient_address
#     value
#     Dict{
#         sender_address
#         recipient_address
#         value
#     }
#     Signature (generated from private key and Dict)
# }

class Transaction:
    def __init__(self, sender_addr, sender_private_key, recipient_addr, value):
        
        self.sender_address = sender_addr
        self.sender_private_key = sender_private_key
        self.recipient_address = recipient_addr
        self.value = value
    @property
    def Dict(self):
        return OrderedDict({
            'sender_address': self.sender_address,
            'recipient_address': self.recipient_address,
            'value': self.value
        })
    @property
    def Signature(self):

        private_key = RSA.importKey(binascii.unhexlify(self.sender_private_key.encode('utf-8')))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.Dict).encode('utf-8'))
        return binascii.hexlify(signer.sign(h))

class BlockChain:
    def __init__(self):
        self.chain = []
        self.ctransactions = []
        self.NewBlock(previous_hash=1, proof=100)
        self.nodes = set()

    #create
    def NewBlock(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.ctransactions,
            'proof': proof,
            'previous_hash':previous_hash or self.Hash(self.chain[-1])
        }
    
        self.ctransactions = []
        self.chain.append(block)
        return block

    def NewTransaction(self, *arg):
        if len(arg) == 1:
            transaction = arg[0]
            self.ctransactions.append(
                {
                    'data': transaction.Dict,
                    'signature': transaction.Signature
                })
        else:
            self.ctransactions.append(
                {
                    'data': {
                        'sender_address': arg[0],
                        'recipient_address': arg[1],
                        'value': arg[2]
                    },
                    'signature':arg[3]
                }
            )
    
    def RegisterNode(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc) 

    #validate
    def ValidTransaction(self, transaction):
        data = transaction['data']
        signature = binascii.unhexlify(transaction['signature'])
        if data!=0 and signature != '':
            h = SHA.new(str(data).encode('utf-8'))
            try:
                PKCS1_v1_5.new(self.public_key).verify(h, signature)
                return True
            except:
                return False
        else:
            return True

    def ValidChain(self, chain):
        # validate the relation between nearest two block by
        # hash and proof
        last_block = chain[0]
        cindex = 1
        while cindex < len(chain):
            block = chain[cindex]
            # validate hash
            if block['previous_hash'] != self.Hash(last_block):
                return False
            # validate proof
            if not self.ValidProof(last_block['proof'], block['proof']):
                return False
            last_block = block
            cindex += 1
        return True

    @staticmethod
    def ValidProof(last_proof, proof):
        # hash begin with 4 zeros (could be customized)
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    def ResolveConflict(self):

        max_length = len(self.chain)
        max_chain = None
        # get the max length chain from neighbor
        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    if length > max_len and self.ValidChain(chain):
                        max_length = length
                        max_chain = chain
            except:
                pass
        
        if max_chain:  # if adopt neighbors chain return True
            self.chain = max_chain
            return True
        return False


    # util
    @staticmethod
    def Hash(block):
        print(block)
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def ProofOfWork(self, last_proof):
        proof = 0
        while self.ValidProof(last_proof, proof) is False:
            proof += 1
        return proof
    
    def CalAmount(self, address):
        amount = 0
        for block in self.chain:
            for t in block['transactions']:
                if t['data']['sender_address'] == address:
                    amount -= t['data']['value']
                elif t['data']['recipient_address'] == address:
                    amount += t['data']['value']
        return amount


