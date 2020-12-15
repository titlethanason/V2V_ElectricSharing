import json
from flask import Flask
app = Flask(__name__)
class BuyerTransaction:
    def __init__(self, idx, buyerIdx, v, vmin, vmax, bmin, bmax):
        self.status = 'pending'
        self.idx = idx
        self.buyerIdx = buyerIdx
        self.v = v
        self.vmax = vmax
        self.vmin = vmin
        self.bmin = bmin
        self.bmax = bmax
        self.agreedTransactionIdx = None
    
    def __repr__(self):
        return "status: {}, idx: {}, buyerIdx: {}, v: {}, vmax: {}, vmin: {}, bmin: {}, bmax: {}".format(self.status,
        self.idx, self.buyerIdx, self.v,  self.vmax, self.vmin, self.bmin, self.bmax) 
    
    def changeStatusToAccepted(self):
        self.status = 'accepted'
        print('Seller transaction: '+str(self.idx)+' , status has been changed to "Accepted"')

    def changeStatusToComplete(self):
        self.status = 'completed'
        print('Buyer transaction: '+str(self.idx)+' , status has been changed to "Completed"')

class SellerTransaction:
    def __init__(self, idx, parentTransactionIdx, sellerIdx, c, cmin, cmax, smin, smax):
        self.status = 'pending'
        self.idx = idx
        self.sellerIdx = sellerIdx
        self.parentTransactionIdx = parentTransactionIdx
        self.c = c
        self.cmax = cmax
        self.cmin = cmin
        self.smin = smin
        self.smax = smax
        self.P = None
        self.R = None
        self.T = None
        self.optimalAmount = None

    def __repr__(self):
        return "status: {}, idx: {}, sellerIdx: {}, parentTransactionIdx: {}, c: {}, cmax: {}, cmin: {}, smin: {}, smax: {}, P: {}, R: {}, T: {}, amount: {} ".format(self.status,
        self.idx, self.sellerIdx, self.parentTransactionIdx, self.c,  self.cmax, self.cmin, self.smin, self.smax, self.P, self.R, self.T, self.optimalAmount)

class Buyer:
    def __init__(self, coordinate, idx):
        self.coordinate = coordinate
        self.idx = idx

    def __repr__(self):
        return "idx: {}, coordinate: {}".format(self.coordinate, self.idx)
    
    def createBuyerTransaction(self, transactionIdx,v, vmin, vmax, bmin, bmax):
        return BuyerTransaction(transactionIdx, self.idx, v, vmin, vmax, bmin, bmax)


class Seller:
    def __init__(self, coordinate, idx):
        self.coordinate = coordinate
        self.idx = idx
    
    def __repr__(self):
        return "idx: {}, coordinate: {}".format(self.coordinate, self.idx)

    def createSellerTransaction(self, transactionIdx, parentTransactionIdx,  c, cmin, cmax, smin, smax):
        return SellerTransaction(transactionIdx, parentTransactionIdx, self.idx,  c, cmin, cmax, smin, smax)

class Auctioneer:
    def __init__(self):
        self.location = []
        self.buyerTransaction = []
        self.sellerTransaction = []
        
    def bt(self): return self.buyerTransaction
    def st(self): return self.sellerTransaction
        
    def fetchBuyerTransaction(self, idx):
        buyerTransaction = None
        for transaction in self.buyerTransaction:
            if(transaction.idx == idx):
                buyerTransaction = transaction
                return buyerTransaction
        if(buyerTransaction == None): 
            print("Can not find buyerTransaction")
            return False
        
    def fetchSellerTransaction(self, idx):
        sellerTransaction = None
        for transaction in self.sellerTransaction:
            if(transaction.idx == idx):
                sellerTransaction = transaction
                return sellerTransaction
        if(sellerTransaction == None): 
            print("Can not find sellerTransaction")
            return False
        
    def computeSellerResponse(self, sellerTransacionIdx):
        sellerTransaction = self.fetchSellerTransaction(sellerTransacionIdx)
        buyerTransaction = self.fetchBuyerTransaction(sellerTransaction.parentTransactionIdx)
        print(buyerTransaction)
        print(sellerTransaction)
        sellerTransaction.P = buyerTransaction.vmax/12 + sellerTransaction.cmin/4 + (2*buyerTransaction.v)/3
        sellerTransaction.R = sellerTransaction.cmin/12 + buyerTransaction.vmax/4 + (2*sellerTransaction.c)/3

        if(sellerTransaction.P < sellerTransaction.R):
            print("Transction failed!")
            sellerTransaction.status = "failed"
            print(sellerTransaction)
            print('----------------------------------------------------')
            return False
        
        sellerTransaction.T = (sellerTransaction.P + sellerTransaction.R)/2
        sellerTransaction.optimalAmount = (((sellerTransaction.cmax - sellerTransaction.c)/sellerTransaction.cmax)*sellerTransaction.smax + ((1-((sellerTransaction.cmax - buyerTransaction.v)/sellerTransaction.cmax))*buyerTransaction.bmax))/2
        print("Transction accepted!")
        sellerTransaction.status = 'accepted'
        print(sellerTransaction)
        print('----------------------------------------------------')
        return True
    
    def completeBuyerTransaction(self, sellerTransactionIdx):
        sellerTransaction = self.fetchSellerTransaction(sellerTransactionIdx)
        buyerTransaction = self.fetchBuyerTransaction(sellerTransaction.parentTransactionIdx)
        if(sellerTransaction.status == 'accepted'):
            sellerTransaction.status = 'complete'
            buyerTransaction.status = 'complete'
            buyerTransaction.agreedTransactionTdx = sellerTransaction.idx
            return True
        else: return False
        
    def getAcceptedTransaction(self, BuyerIdx):
        sellerTransaction = []
        for transaction in self.sellerTransaction:
            if(transaction.parentTransactionIdx == BuyerIdx and transaction.status == 'accepted'):
                sellerTransaction.append(transaction)
    
        if(sellerTransaction == None): return False
        else : return [ transaction.__dict__ for transaction in sellerTransaction ]
    
    def getBuyerPendingTransaction(self, idx):
        b_transaction = []
        for buyerTransaction in [transaction.__dict__ for transaction in self.buyerTransaction if transaction.buyerIdx == idx]:
            b_transaction.append(buyerTransaction)
            for sellerTransaction in [transaction.__dict__ for transaction in self.sellerTransaction if transaction.parentTransactionIdx == buyerTransaction['idx'] and transaction.status == 'accepted']:
                b_transaction.append(sellerTransaction)
        return b_transaction
    
    def getBuyerCompletedTransaction(self, idx):
        b_transaction = []
        for buyerTransaction in [transaction.__dict__ for transaction in self.buyerTransaction if transaction.buyerIdx == idx]:
            if(buyerTransaction['status'] == 'complete'):
                b_transaction.append(buyerTransaction)
        return b_transaction
    
    def getSellerPendingTransaction(self, idx):
        b_transaction = []
        s_transactionIdxs = [sellerTransaction.idx for sellerTransaction in self.sellerTransaction if sellerTransaction.idx == idx]
        for buyerTransaction in self.buyerTransaction:
            if( (buyerTransaction.idx not in s_transactionIdxs) and (buyerTransaction.status == 'pending')):
                b_transaction.append(buyerTransaction.__dict__)
        return b_transaction
    
    def getSellerAcceptedTransaction(self, idx):
        return [ transaction.__dict__ for transaction in self.sellerTransaction if transaction.status == 'accepted' and transaction.sellerIdx == idx]
    
    def getSellerCompleltedFailedTransaction(self, idx):
        return [ transaction.__dict__ for transaction in self.sellerTransaction if transaction.status in ['completed', 'failed'] and transaction.sellerIdx == idx]
    
    def getAuctioneerPendingTransaction(self):
        pendingTransaction = [transaction.__dict__ for transaction in self.buyerTransaction if transaction.status == 'pending']
        acceptedTransaction = [transaction.__dict__ for transaction in self.sellerTransaction if transaction.status == 'accepted']
        return pendingTransaction+acceptedTransaction
    
    def getAuctioneerCompletedTransaction(self):
        return [transaction.__dict__ for transaction in self.buyerTransaction if transaction.status == 'completed']
    
    def getAuctioneerFailedTransaction(self):
        return [transaction.__dict__ for transaction in self.sellerTransaction if transaction.status == 'failed']

    def createBuyerTransaction(self, transactionIdx, buyerIdx, v, vmin, vmax, bmin, bmax):
        newTransaction = BuyerTransaction(transactionIdx, buyerIdx, v, vmin, vmax, bmin, bmax)
        self.buyerTransaction.append(newTransaction)
        return True
    
    def createSellerTransaction(self, transactionIdx, parentTransactionIdx, sellerIdx,  c, cmin, cmax, smin, smax):
        newTransaction = SellerTransaction(transactionIdx, parentTransactionIdx, sellerIdx,  c, cmin, cmax, smin, smax)
        self.sellerTransaction.append(newTransaction)
        self.computeSellerResponse(newTransaction.idx)
        return True

dummyBuyerTransaction = [BuyerTransaction(1, 1, v=10, vmin=1, vmax=10, bmin=30, bmax=150),
    BuyerTransaction(2, 1, v=10, vmin=2, vmax=20, bmin=10, bmax=100),
    BuyerTransaction(3, 2, v=30, vmin=3, vmax=30, bmin=20, bmax=200),
    BuyerTransaction(4, 1, v=40, vmin=4, vmax=40, bmin=30, bmax=300),
    BuyerTransaction(5, 5, v=50, vmin=5, vmax=50, bmin=40, bmax=400)]
    
dummySellerTransaction = [SellerTransaction(1, 1, 1, c=3, cmin=1, cmax=30, smin=30, smax=150),
    SellerTransaction(2, 1, 2, c=5, cmin=2, cmax=20, smin=10, smax=100),
    SellerTransaction(3, 3, 3, c=1, cmin=3, cmax=30, smin=20, smax=200),
    SellerTransaction(4, 4, 4, c=40, cmin=4, cmax=40, smin=30, smax=300),
    SellerTransaction(5, 5, 5, c=50, cmin=5, cmax=50, smin=40, smax=400)]

auctioneer = Auctioneer()
auctioneer.buyerTransaction = dummyBuyerTransaction
auctioneer.sellerTransaction = dummySellerTransaction
for transaction in auctioneer.sellerTransaction:
    auctioneer.computeSellerResponse(transaction.idx)

@app.route('/<id>')
def index(id):
    global auctioneer
    output = auctioneer.getBuyerPendingTransaction(int(id))
    return str(output)

if __name__ == '__main__':
  app.debug = True
  app.run(host='127.0.0.1', port=8000)	
        