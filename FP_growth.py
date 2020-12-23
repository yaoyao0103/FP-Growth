import time
from itertools import combinations

############################import data and transform dtype to frozenset###################################

def loadDataSet_int():
    with open("mushroom.dat", 'r') as f:
        dataSet = []
        for line in f:
            dataSet.append([int(x) for x in line.split()])
    return dataSet 

def loadDataSet_str():
    with open("mushroom.dat", 'r') as f:
        dataSet = [line.split() for line in f.readlines()]
    return dataSet
    
def loadDataSet_test():    
    dataSet = [['f','a','c','d','g','i','m','p'], 
               ['a','b','c','f','l','m','o'], 
               ['b','f','h','j','o'], 
               ['b','c','k','s','p'], 
               ['a','f','c','e','l','p','m','n']]
    return dataSet

def transfer2FrozenDataSet(dataSet):
    frozenDataSet = {}
    for elem in dataSet:
        frozenDataSet[frozenset(elem)] = 1
    return frozenDataSet

#############################FPtree node結構結構###################################
class TreeNode:
    def __init__(self, nodeName, count, nodeParent):
        self.nodeName = nodeName
        self.count = count
        self.nodeParent = nodeParent
        self.nextSimilarItem = None
        self.children = {}

    def increaseC(self, count):
        self.count += count
        
    def disp(self, ind=1):  ##印出樹
        print ('  '*ind, self.nodeName, ' ', self.count)
        for child in self.children.values():
            child.disp(ind+1)  
            
#################################建FP樹###################################

def createFPTree(frozenDataSet, minSupport):
   
    headPointTable = {}
    for items in frozenDataSet:
        for item in items:
            headPointTable[item] = headPointTable.get(item, 0) + frozenDataSet[items]  ##統計次數
    headPointTable = {k:v for k,v in headPointTable.items() if v >= minSupport}  ##篩選minSupport
    frequentItems = set(headPointTable.keys())
    if len(frequentItems) == 0: return None, None

    for k in headPointTable:
        headPointTable[k] = [headPointTable[k], None]  ##將headPointTable value轉乘list，第一格放次數，第二格放nextSimilarItem
    fptree = TreeNode("null", 1, None)
    
    for items,count in frozenDataSet.items():
        frequentItemsInRecord = {}
        for item in items:
            if item in frequentItems:
                frequentItemsInRecord[item] = headPointTable[item][0]  ##過濾data
        if len(frequentItemsInRecord) > 0:
            #orderedFrequentItems = [v[0] for v in sorted(frequentItemsInRecord.items(), key=lambda v:v[1], reverse = True)]
            orderedFrequentItems = [v[0] for v in sorted(frequentItemsInRecord.items(), key=lambda v:(v[1], v[0]), reverse = True)]  ##排序dataSet
            updateFPTree(fptree, orderedFrequentItems, headPointTable, count)

    return fptree, headPointTable

def updateFPTree(fptree, orderedFrequentItems, headPointTable, count):  ##更新樹
    #handle the first item
    if orderedFrequentItems[0] in fptree.children:
        fptree.children[orderedFrequentItems[0]].increaseC(count)  ##count增加
    else:
        fptree.children[orderedFrequentItems[0]] = TreeNode(orderedFrequentItems[0], count, fptree)  ##新增新的node

        if headPointTable[orderedFrequentItems[0]][1] == None:  ##更新headPointTable
            headPointTable[orderedFrequentItems[0]][1] = fptree.children[orderedFrequentItems[0]]   ##指到這個
        else:
            updateHeadPointTable(headPointTable[orderedFrequentItems[0]][1], fptree.children[orderedFrequentItems[0]])  ##找到最後一個，再把這個塞入最後一個
    
    if(len(orderedFrequentItems) > 1):
        updateFPTree(fptree.children[orderedFrequentItems[0]], orderedFrequentItems[1::], headPointTable, count)  ##遞迴，往下一個

def updateHeadPointTable(headPointBeginNode, targetNode):  ##更新headPointTabl需要的函式
    while(headPointBeginNode.nextSimilarItem != None):  ##找到最後一個，再把targetNode塞入最後一個
        headPointBeginNode = headPointBeginNode.nextSimilarItem
    headPointBeginNode.nextSimilarItem = targetNode

##############################挖掘frequentPatterns###################################

def mineFPTree(headPointTable, prefix, frequentPatterns, minSupport, maxPatLen):
    if len(prefix) >= maxPatLen: return  ##大於maxPatLen，return
    headPointItems = [v[0] for v in sorted(headPointTable.items(), key = lambda v:v[1][0])]  ##排序，轉為list
    if(len(headPointItems) == 0): return

    for headPointItem in headPointItems:  ##找所有headPointItems的路徑
        newPrefix = prefix.copy()
        newPrefix.add(headPointItem)
        frequentPatterns[frozenset(newPrefix)] = headPointTable[headPointItem][0]  ##key為frozenset型態的newPrefix, value為headPointItem在headPointTable的value

        prefixPath = getPrefixPath(headPointTable, headPointItem)
        if(prefixPath != {}):
            conditionalFPtree, conditionalHeadPointTable = createFPTree(prefixPath, minSupport)  ##創造新樹，回傳新root，HeadPointTable
            if conditionalHeadPointTable != None:
                mineFPTree(conditionalHeadPointTable, newPrefix, frequentPatterns, minSupport, maxPatLen)  ##繼續遞迴

#################################前綴路境###################################

def getPrefixPath(headPointTable, headPointItem):  ##找nextSimilarItem 再傳入ascendTree函式找路徑
    prefixPath = {}
    beginNode = headPointTable[headPointItem][1]
    prefixs = ascendTree(beginNode)
    if((prefixs != [])):
        prefixPath[frozenset(prefixs)] = beginNode.count  ##路徑為frozenset型態的key，路徑數量為value

    while(beginNode.nextSimilarItem != None):  ##nextSimilarItem不為空，則往下一個nextSimilarItem走
        beginNode = beginNode.nextSimilarItem
        prefixs = ascendTree(beginNode)
        if (prefixs != []):
            prefixPath[frozenset(prefixs)] = beginNode.count
    return prefixPath

def ascendTree(treeNode):  ##往上找路徑
    prefixs = []
    while((treeNode.nodeParent != None) and (treeNode.nodeParent.nodeName != 'null')):
        treeNode = treeNode.nodeParent  ##往父節點走
        prefixs.append(treeNode.nodeName)
    return prefixs


###############################挖掘關聯規則########################################
                    
def associaton_rules(frequentPatterns, minConf):
    total = 0
    for freqenceItem in frequentPatterns:
        subSets = [c for n in range(1, len(freqenceItem)) for c in combinations(freqenceItem, n)]  ##從頻繁項集生成所有排列組合子集合

        for subSet in subSets:
            confidence = float(frequentPatterns[frozenset(freqenceItem)] / frequentPatterns[frozenset(subSet)])

            if (confidence >= minConf):
                total += 1
                #yield set(subSet), set(freqenceItem) - set(subSet), confidence  ##assocition rules
    print("association rules total:", total)            

#############################test print##############################
                
def ht_print(headPointTable):  ##headPointTable print
    print(len(headPointTable))
    for x, y in headPointTable.items():
       print(x,"=", y[0])                
                
def fp_print(frequentPatterns):  ##frequencePatterns print
    for x in frequentPatterns:
       print(list(x),"=", frequentPatterns[x])
       
def rule_print(rules):  ##association rules print
    for x in rules:
        #print("%s=>%s" % (list(x[0]) list(x[1]))
        print(list(x[0]),"=>", list(x[1]), "=", x[2])
        
def count_frequence_item_set(frequentPatterns):  ##計算frequence item set
    count = [0,0,0,0,0,0]
    for item in frequentPatterns:
        count[len(item)]+=1
    for i in range(1,len(count)):
        print("|L^{}|={}".format(i,count[i]))
    
############################main##############################

if __name__=='__main__':
    begin = time.time()
    dataSet = loadDataSet_str()
    #print(dataSet)
    print("data num:", len(dataSet))
    minSupport = (len(dataSet)+9)//10
    minConf = 0.8
    maxPatLen = 5
    print("minSupport=", minSupport)  ##support限制
    print("minConf=", minConf)  ##confidence限制
    print("maxPatLen num:", maxPatLen)  ##frequence patterns rules長度限制
    frozenDataSet = transfer2FrozenDataSet(dataSet)  ##換成frozenset
    fptree, headPointTable = createFPTree(frozenDataSet, minSupport)  ##建樹
    #print("fptree:")
    #fptree.disp()
    #ht_print(headPointTable)
    
    frequentPatterns = {}
    prefix = set([])
    mineFPTree(headPointTable, prefix, frequentPatterns, minSupport, maxPatLen)  ##挖掘
    #print("frequent patterns:")
    #fp_print(frequentPatterns)
    count_frequence_item_set(frequentPatterns)   ##計算frequence item set
    associaton_rules(frequentPatterns, minConf)
    end = time.time()
    print("execute time:", end-begin)