from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap
import haversine as hs
import json
app = Flask(__name__)
Bootstrap(app)

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
        self.T = None
        self.distance = None
        self.optimalAmount = None
    
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
        self.distance = None

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
        self.countBuyerTransaction = 5
        self.countSellerTransaction = 5
        self.buyers = []
        self.sellers = []
        
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
    
    def fetchSellerTransactionsByParentTransactionIdx(self, parentTransactionIdx):
        return [transaction for transaction in self.sellerTransaction if transaction.parentTransactionIdx == parentTransactionIdx]
    
        
    def computeSellerResponse(self, sellerTransacionIdx):
        sellerTransaction = self.fetchSellerTransaction(sellerTransacionIdx)
        buyerTransaction = self.fetchBuyerTransaction(sellerTransaction.parentTransactionIdx)
        sellerLocation = self.sellers[sellerTransaction.sellerIdx-1].coordinate
        buyerLocation = self.buyers[buyerTransaction.buyerIdx-1].coordinate
        sellerTransaction.distance = round(hs.haversine(sellerLocation,buyerLocation), 2)
        print("distance = "+str(sellerTransaction.distance)+" km")

        print(buyerTransaction)
        print(sellerTransaction)
        sellerTransaction.P = round(buyerTransaction.vmax/12 + sellerTransaction.cmin/4 + (2*buyerTransaction.v)/3,2)
        sellerTransaction.R = round(sellerTransaction.cmin/12 + buyerTransaction.vmax/4 + (2*sellerTransaction.c)/3)

        if((sellerTransaction.P < sellerTransaction.R) or (sellerTransaction.smin > buyerTransaction.bmax) or (buyerTransaction.bmin > serllerTransaction.smax)):
            print("Transction failed!")
            sellerTransaction.status = "failed"
            print(sellerTransaction)
            print('----------------------------------------------------')
            return False
        
        sellerTransaction.T = (sellerTransaction.P + sellerTransaction.R)/2
        sellerTransaction.optimalAmount = round((((sellerTransaction.cmax - sellerTransaction.c)/sellerTransaction.cmax)*sellerTransaction.smax + ((1-((sellerTransaction.cmax - buyerTransaction.v)/sellerTransaction.cmax))*buyerTransaction.bmax))/2)
        print("Transction accepted!")
        sellerTransaction.status = 'accepted'
        print(sellerTransaction)
        print('----------------------------------------------------')
        return True
    
    def completeBuyerTransaction(self, sellerTransactionIdx):
        sellerTransaction = self.fetchSellerTransaction(sellerTransactionIdx)
        buyerTransaction = self.fetchBuyerTransaction(sellerTransaction.parentTransactionIdx)
        if(sellerTransaction.status == 'accepted'):
            sellerTransaction.status = 'completed'
            buyerTransaction.status = 'completed'
            buyerTransaction.agreedTransactionIdx = sellerTransaction.idx
            buyerTransaction.T = sellerTransaction.T
            buyerTransaction.distance = sellerTransaction.distance
            buyerTransaction.optimalAmount = sellerTransaction.optimalAmount
            for transaction in self.fetchSellerTransactionsByParentTransactionIdx(sellerTransaction.parentTransactionIdx):
                if(transaction.idx != sellerTransaction.idx):
                    transaction.status = 'failed'
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
        for buyerTransaction in [transaction.__dict__ for transaction in self.buyerTransaction if transaction.buyerIdx == idx and transaction.status == 'pending']:
            b_transaction.append(buyerTransaction)
            for sellerTransaction in [transaction.__dict__ for transaction in self.sellerTransaction if transaction.parentTransactionIdx == buyerTransaction['idx'] and transaction.status == 'accepted']:
                b_transaction.append(sellerTransaction)
        return b_transaction
    
    def getBuyerCompletedTransaction(self, idx):
        b_transaction = []
        for buyerTransaction in [transaction.__dict__ for transaction in self.buyerTransaction if transaction.buyerIdx == idx]:
            if(buyerTransaction['status'] == 'completed'):
                b_transaction.append(buyerTransaction)
        return b_transaction
    
    def getSellerPendingTransaction(self, idx):
        b_transaction = []
        sellerLocation = self.sellers[idx-1].coordinate
        s_transactionIdxs = [sellerTransaction.parentTransactionIdx for sellerTransaction in self.sellerTransaction if sellerTransaction.sellerIdx == idx]
        for buyerTransaction in self.buyerTransaction:
            if( (buyerTransaction.idx not in s_transactionIdxs) and (buyerTransaction.status == 'pending')):
                buyerLocation = self.buyers[buyerTransaction.buyerIdx-1].coordinate
                distance = round(hs.haversine(sellerLocation,buyerLocation), 2)
                buyerTransactionDict = buyerTransaction.__dict__
                buyerTransactionDict['distance'] = distance
                b_transaction.append(buyerTransactionDict)
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

buyers = [Buyer((13.7203636, 100.4983167), 1), Buyer((13.7210854,100.4952133), 2), Buyer((13.7057435,100.4809689), 3), Buyer((13.6562446,100.4817984), 4), Buyer((13.7213584,100.5305075), 5)]
sellers = [Seller((13.651362879156872,100.49486250045186),1), Seller((13.7057435,100.4809689), 2), Seller((13.6562446,100.4817984), 3), Seller((13.7213584,100.5305075), 4), Seller((13.7277753,100.5352955), 5)]

auctioneer = Auctioneer()
auctioneer.buyers = buyers
auctioneer.sellers = sellers
auctioneer.buyerTransaction = dummyBuyerTransaction
auctioneer.sellerTransaction = dummySellerTransaction
for transaction in auctioneer.sellerTransaction:
    auctioneer.computeSellerResponse(transaction.idx)
#auctioneer.completeBuyerTransaction(1)

@app.route('/buyer/<id>')
def buyer(id):
    global auctioneer
    pending = auctioneer.getBuyerPendingTransaction(int(id))
    complete = auctioneer.getBuyerCompletedTransaction(int(id))
    print(pending)
    return render_template('buyer.html',title='buyer',id=id, pending=pending,complete=complete)

@app.route('/seller/<id>')
def seller(id):
    pending = auctioneer.getSellerPendingTransaction(int(id))
    accept = auctioneer.getSellerAcceptedTransaction(int(id))
    complete = auctioneer.getSellerCompleltedFailedTransaction(int(id))
    return render_template('seller.html',title='seller',id=id, pending=pending,accept=accept,complete=complete)

@app.route('/auctioneer/<id>')
def index(id):
    pending = auctioneer.getAuctioneerPendingTransaction()
    complete = auctioneer.getAuctioneerCompletedTransaction()
    fail = auctioneer.getAuctioneerFailedTransaction()
    return render_template('auctioneer.html',title='auctioneer',id=id,pending=pending,complete=complete)

@app.route('/create/<id>', methods=['POST'])
def create(id):
    global auctioneer
    v = request.form['v']
    vmin = request.form['vmax']
    vmax = request.form['vmax']
    bmin = request.form['bmin']
    bmax = request.form['bmax']
    auctioneer.countBuyerTransaction = auctioneer.countBuyerTransaction+1
    auctioneer.createBuyerTransaction(auctioneer.countBuyerTransaction, int(id), int(v), int(vmin), int(vmax), int(bmin), int(bmax))

    return redirect('/buyer/'+id)

@app.route('/response/<id>', methods=['POST'])
def response(id):
    global auctioneer
    c = request.form['c']
    cmin = request.form['cmax']
    cmax = request.form['cmax']
    smin = request.form['smin']
    smax = request.form['smax']
    parentIdx= request.form['idx']
    print('{} {} {} {} {} {}'.format(c,cmin,cmax,smin,smax,parentIdx))
    auctioneer.countSellerTransaction = auctioneer.countSellerTransaction+1
    auctioneer.createSellerTransaction(auctioneer.countSellerTransaction, int(parentIdx), int(id), int(c), int(cmin), int(cmax), int(smin), int(smax))

    return redirect('/seller/'+id)


@app.route('/confirmBuyerTransaction/<id>', methods=['POST'])
def confirmBuyerTransaction(id):
    global auctioneer
    sellerTransactionIdx = int(request.form['idx'])
    auctioneer.completeBuyerTransaction(sellerTransactionIdx)
    return redirect('/buyer/'+id)

@app.route('/bt')
def bt():
    global auctioneer
    return str(auctioneer.getBuyerPendingTransaction(1))

if __name__ == '__main__':
    app.run(debug=True)	