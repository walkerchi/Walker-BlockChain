from BlockChain import *
from Config import *

import os
import pickle as pkl
from time import time
from uuid import uuid1
from textwrap import dedent
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests




# instantiate the node
app = Flask(__name__,static_url_path='')
# CORS(app)

# unique id for this node
if not os.path.exists('/uuid'):
    node_identifier = str(uuid1()).replace('-', '')
    with open('/uuid', 'wb') as f:
        pkl.dump(node_identifier, f)
else:
    with open('/uuid', 'rb') as f:
        node_identifier = pkl.load(f)
    

blockchain = BlockChain()



@app.after_request
def cors(env):
    env.headers['Access-Control-Allow-Origin']='*'
    env.headers['Access-Control-Allow-Method']='*'
    env.headers['Access-Control-Allow-Headers']='x-requested-with,content-type'
    return env

@app.route('/')
@app.route('/index')
def index():
    return app.send_static_file('index.html')
    # return render_template('/index.html')

#create wallet
@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    random_gen = Random.new().read
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.publickey()
    blockchain.public_key = public_key
    blockchain.private_key = private_key
    response = {
        'message': 'WALLET CREATED',
        'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
        'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    }
    return jsonify(response),200

# create transaction
    # request{
    #     'sender_address': 'address'
    #     'sender_private_key':key
    #     'recipient_address': 'another address'
    #     'amount':5
    # }
@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = dict(request.form)
    print(values)
    try:
        sender_addr = values['senderAddress']
        sender_privatekey = values['senderPrivateKey']
        recipient_addr = values['recipientAddress']
        value = eval(values['amount'])
    except:
        return 'POST ERROR',400
        
    transaction = Transaction(sender_addr,sender_privatekey,recipient_addr,value)

    if not blockchain.ValidTransaction(transaction):
        return 'VALID ERROR',401

    blockchain.NewTransaction(transaction)
    
    response = {'message': f'Transaction will be added to Block{index}',
                'transaction':transaction.Dict,
                'signature': transaction.Signature
                }
    return jsonify(response),201

@app.route('/address/get', methods=['GET'])
def get_address():
    response = {
            'message':'HERE YOUR ARE',
            'address':node_identifier}
    return jsonify(response),200

# get transactions
@app.route('/transaction/get', methods=['GET'])
def get_transactions():
    transactions = blockchain.transactions
    response = {
        'length':len(transactions),
        'transactions':transactons}
    return jsonify(response),200

# get chains
@app.route('/chain/get', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length':len(blockchain.chain),
    }
    return jsonify(response), 200
    
@app.route('/amount/get', methods=['GET'])
def get_amount():
    amount = blockchain.CalAmount(node_identifier)
    response = {
        'message': 'HERE YOUR ARE',
        'amount': amount
    }
    return jsonify(response),200

# mine block
@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.chain[-1]
    last_proof = last_block['proof']
    proof = blockchain.ProofOfWork(last_proof)

    # reward  a coin
    blockchain.NewTransaction(MINEING_SENDER,
    node_identifier,
    MINEING_REWARD,
    '')
    
    previous_hash = blockchain.Hash(last_block)
    block = blockchain.NewBlock(proof, previous_hash)
    
    response = {
        'message': 'NEW BLOCK FORGED',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash':block['previous_hash'],
    }
    return jsonify(response),200


# request{
    #     'nodes':[address(url)]
    # }
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    print(request.form)
    values = dict(request.form)
    nodes = values['nodes']
    if nodes is None:
        return "NODE REGISTER ERROR", 400
    nodes = nodes.split(',')
    print(nodes)
    for node in nodes:
        blockchain.RegisterNode(node)
    
    response = {
        'message': 'NEW NODES ADDED',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response),201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    is_renewed = blockchain.ResolveConflict()
    if is_renewed:
        response = {
            'message': 'CHAIN RENEWED FROM NEIGHBORS',
            'chain':blockchain.chain
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'CHAIN iS AUTHORITATIVE',
            'chain':blockchain.chain
        }
        return jsonify(response), 200

@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes}
    return jsonify(response),200



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=PORT)
    