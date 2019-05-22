from flask import render_template, flash, redirect, url_for, request, jsonify
from collections import defaultdict
import sqlite3
import json
import os
from flask import Flask
from flask_cors import CORS

dbfolder = ''
app = Flask(__name__)
CORS(app)


# FLO TOKEN APIs

@app.route('/api/v1.0/gettokenlist', methods=['GET'])
def gettokenlist():
    filelist = []
    for item in os.listdir(os.path.join(dbfolder,'tokens')):
        if os.path.isfile(os.path.join(dbfolder, 'tokens', item)):
            filelist.append(item[:-3])

    return jsonify(tokens = filelist, result='ok')

@app.route('/api/v1.0/getaddressbalance', methods=['GET'])
def getaddressbalance():
    address = request.args.get('address')
    token = request.args.get('token')

    if address is None or token is None:
        return jsonify(result='error')

    dblocation = dbfolder + token + '.db'
    if os.path.exists(dblocation):
        conn = sqlite3.connect(dblocation)
        c = conn.cursor()
    else:
        return 'Token doesn\'t exist'
    c.execute('SELECT SUM(transferBalance) FROM activeTable WHERE address="{}"'.format(address))
    balance = c.fetchall()[0][0]
    conn.close()
    return jsonify(result='ok', token=token, address=address, balance=balance)


@app.route('/api/v1.0/gettokeninfo', methods=['GET'])
def gettokeninfo():
    token = request.args.get('token')

    if token is None:
        return jsonify(result='error')

    dblocation = dbfolder + token + '.db'
    if os.path.exists(dblocation):
        conn = sqlite3.connect(dblocation)
        c = conn.cursor()
    else:
        return 'Token doesn\'t exist'
    c.execute('SELECT * FROM transactionHistory WHERE id=1')
    incorporationRow = c.fetchall()[0]
    c.execute('SELECT COUNT (DISTINCT address) FROM activeTable')
    numberOf_distinctAddresses = c.fetchall()[0][0]
    conn.close()
    return jsonify(result='ok', token=token, incorporationAddress=incorporationRow[2], tokenSupply=incorporationRow[3],
                   transactionHash=incorporationRow[6], blockchainReference=incorporationRow[7],
                   activeAddress_no=numberOf_distinctAddresses)


@app.route('/api/v1.0/gettransactions', methods=['GET'])
def gettransactions():
    token = request.args.get('token')
    senderFloAddress = request.args.get('senderFloAddress')
    destFloAddress = request.args.get('destFloAddress')

    if token is None:
        return jsonify(result='error')

    dblocation = dbfolder + token + '.db'
    if os.path.exists(dblocation):
        conn = sqlite3.connect(dblocation)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
    else:
        return 'Token doesn\'t exist'

    if senderFloAddress and not destFloAddress:
        c.execute(
            'SELECT blockNumber, sourceFloAddress, destFloAddress, transferAmount, blockchainReference FROM transactionHistory WHERE sourceFloAddress="{}" ORDER BY id DESC LIMIT 100'.format(
                senderFloAddress))
    if not senderFloAddress and destFloAddress:
        c.execute(
            'SELECT blockNumber, sourceFloAddress, destFloAddress, transferAmount, blockchainReference FROM transactionHistory WHERE destFloAddress="{}" ORDER BY id DESC LIMIT 100'.format(
                destFloAddress))
    if senderFloAddress and destFloAddress:
        c.execute(
            'SELECT blockNumber, sourceFloAddress, destFloAddress, transferAmount, blockchainReference FROM transactionHistory WHERE sourceFloAddress="{}" OR destFloAddress="{}" ORDER BY id DESC LIMIT 100'.format(
                senderFloAddress, destFloAddress))

    else:
        c.execute(
            'SELECT blockNumber, sourceFloAddress, destFloAddress, transferAmount, blockchainReference FROM transactionHistory ORDER BY id DESC LIMIT 100')
    latestTransactions = c.fetchall()
    conn.close()
    rowarray_list = []
    for row in latestTransactions:
        d = dict(zip(row.keys(), row))  # a dict with column names as keys
        rowarray_list.append(d)
    return jsonify(result='ok', transactions=rowarray_list)

# SMART CONTRACT APIs

@app.route('/api/v1.0/getsmartContractlist', methods=['GET'])
def getcontractlist():
    filelist = []
    for item in os.listdir(os.path.join(dbfolder,'smartContracts')):
        if os.path.isfile(os.path.join(dbfolder, 'smartContracts', item)):
            filelist.append(item[:-3])

    return jsonify(smartContracts = filelist, result='ok')

@app.route('/api/v1.0/getsmartContractinfo', methods=['GET'])
def getcontractinfo():
    name = request.args.get('name')
    contractAddress = request.args.get('contractAddress')

    if name is None:
        return jsonify(result='error', details='Smart Contract\'s name hasn\'t been passed')

    if contractAddress is None:
        return jsonify(result='error', details='Smart Contract\'s address hasn\'t been passed')

    contractName = '{}-{}.db'.format(name.strip(),contractAddress.strip())
    filelocation = os.path.join(dbfolder,'smartContracts', contractName)

    if os.path.isfile(filelocation):
        #Make db connection and fetch data
        conn = sqlite3.connect(filelocation)
        c = conn.cursor()
        c.execute(
            'SELECT attribute,value FROM contractstructure')
        result = c.fetchall()

        returnval = {'exitconditions': []}
        temp = 0
        for row in result:
            if row[0] == 'exitconditions':
                if temp == 0:
                    returnval["exitconditions"] = [row[1]]
                    temp = temp + 1
                else:
                    returnval['exitconditions'].append(row[1])
                continue
            returnval[row[0]] = row[1]

        c.execute('select count(participantAddress) from contractparticipants')
        noOfParticipants = c.fetchall()[0][0]
        returnval['numberOfParticipants'] = noOfParticipants

        c.execute('select sum(tokenAmount) from contractparticipants')
        totalAmount = c.fetchall()[0][0]
        returnval['tokenAmountDeposited'] = totalAmount

        conn.close()
        return jsonify(result='ok', contractInfo=returnval)

    else:
        return jsonify(result='error', details='Smart Contract with the given name doesn\'t exist')

    #return jsonify('smartContracts' : filelist, result='ok')

@app.route('/api/v1.0/getsmartContractparticipants', methods=['GET'])
def getcontractparticipants():
    name = request.args.get('name')
    contractAddress = request.args.get('contractAddress')

    if name is None:
        return jsonify(result='error', details='Smart Contract\'s name hasn\'t been passed')

    if contractAddress is None:
        return jsonify(result='error', details='Smart Contract\'s address hasn\'t been passed')

    contractName = '{}-{}.db'.format(name.strip(),contractAddress.strip())
    filelocation = os.path.join(dbfolder,'smartContracts', contractName)

    if os.path.isfile(filelocation):
        #Make db connection and fetch data
        conn = sqlite3.connect(filelocation)
        c = conn.cursor()
        c.execute(
            'SELECT id,participantAddress, tokenAmount, userChoice FROM contractparticipants')
        result = c.fetchall()
        conn.close()
        returnval = {}
        for row in result:
            returnval[row[0]] = [row[1],row[2],row[3]]

        return jsonify(result='ok', participantInfo=returnval)

    else:
        return jsonify(result='error', details='Smart Contract with the given name doesn\'t exist')

@app.route('/api/v1.0/getparticipantdetails', methods=['GET'])
def getParticipantDetails():
    floaddress = request.args.get('floaddress')

    if name is floaddress:
        return jsonify(result='error', details='FLO address hasn\'t been passed')

    filelocation = os.path.join(dbfolder,'system.db')

    if os.path.isfile(filelocation):
        #Make db connection and fetch data
        conn = sqlite3.connect(filelocation)
        c = conn.cursor()
        c.execute(
            'SELECT id,participantAddress, tokenAmount, userChoice FROM contractparticipants')
        result = c.fetchall()
        conn.close()
        returnval = {}
        for row in result:
            returnval[row[0]] = [row[1],row[2],row[3]]

        return jsonify(result='ok', participantInfo=returnval)

    else:
        return jsonify(result='error', details='Smart Contract with the given name doesn\'t exist')


@app.route('/test')
def test():
    return render_template('test.html')

if __name__ == "__main__":
    app.run(debug=True)

