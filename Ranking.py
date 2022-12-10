import json
import math
from queue import PriorityQueue

invertedIndexFile = open("invertedIndex.json")
invertedIndex = json.load(invertedIndexFile)

inputFile = open("shakespeare-scenes.json")
fileData = json.load(inputFile)
dataset = fileData["corpus"]
#for term in invertedIndex:
#    print(term)
    
#returns Postings List of a term
def getPostings(term):
    if term not in invertedIndex:
        return None
    return invertedIndex[term]
#print(getPostings("venice"))

#returns frequency of term in collection (number of times term appears in total)
def getTermFreq(term):
    postings = getPostings(term)
    totalCount = 0
    for posting in postings:
        totalCount += len(posting[1])
    return totalCount
#print(getTermFreq("venice"))

#returns number of documents containing a term
def getDocFreq(term):
    return len(getPostings(term))
#print(getDocFreq("venice"))

#returns total word count in collection
def getCollectionSize():
    totalCount = 0
    for term in invertedIndex:
        postings = invertedIndex[term]
        for posting in postings:
            positions = posting[1]
            totalCount += len(positions)
    return totalCount
#print(getCollectionSize())

#returns length of document given docID
def getDocLength(docID):
    docText = dataset[docID-1]["text"].split(" ")
    wordCount = 0
    for word in docText:
        if len(word) >= 1:
            wordCount += 1
    return wordCount
#print(getDocLength(1))

#returns number of documents
def getDocCount():
    return len(dataset)
#print(getDocCount())

#returns average length of a document
def getAverageDocLength():
    return float(getCollectionSize())/float(getDocCount())
#print(getAverageDocLength())

#returns all terms in vocabulary, unordered
def getVocabulary():
    return list(invertedIndex.keys())
#print(getVocabulary())

def getDocsByTerm(term):
    postings = getPostings(term)
    docs = []
    for posting in postings:
        docs.append(posting[0])
    return docs
#print(getDocsByTerm("venice"))

def getTermFreqDoc(term, doc):
    postings = getPostings(term)
    for posting in postings:
        if posting[0] == doc:
            return len(posting[1])
    return 0
#for i in range(1, 20):
#    print(getTermFreqDoc("venice", i))

def filterDocs(query):
    terms = query.split(" ")
    docs = []
    for term in terms:
        docs.append(getDocsByTerm(term))
    return list(set.intersection(*map(set, docs)))
#print(filterDocs("venice"))

#returns list of documents containing terms as ordered phrase, given string: query
#output: {docId: frequency}

def getPositions(term, doc):
    if term not in invertedIndex:
        return None
    postings = getPostings(term)
    for posting in postings:
        if posting[0] == doc:
            return posting[1]
    return None

def getTermDocFreq(term, doc):
    if getPositions(term, doc) == None:
        return 0
    return len(getPositions(term, doc))
#print(getTermDocFreq("venice", 1))

def retrieveQuery(query):
    filteredDocs = sorted(filterDocs(query))
    terms = query.split(" ")
    results = []
    for doc in filteredDocs:
        firstTermPositions = getPositions(terms[0], doc)
        count = 0
        for pos in firstTermPositions:
            query_found = True
            for i in range(len(terms)):
                cureTermPositions = getPositions(terms[i], doc)
                if pos + i not in cureTermPositions:
                    query_found = False
                    break
            if query_found == True:
                count += 1
        results.append((doc, count))
    return results
#print(getDocsByTerm("venice"))
#print(retrieveQuery("venice"))

def getPlayId(key):
    return dataset[key-1]["playId"]
#print(getPlayId(16))

def getSceneId(key):
    return dataset[key-1]["sceneId"]
#print(getSceneId(16))

#########################
# start of ranking

k1 = 1.8
k2 = 5.0
b = 0.75
mu = 250.0
avdl = float(getAverageDocLength())
R = 0.0
ri = 0.0
N = float(getDocCount())
C = float(getCollectionSize())

def K_calc(dl):
    K = k1 * ( (1-b) + b *(float(dl)/float(avdl)) )
    return K
#ni = # docs containing term i, N = number of documents in collection, fi = frequency of term i in document, qfi = frequency of term in query
# inputs should be: ni, fi, qfi, K
def BM25_calc(ni, fi, qfi, K):
    factor1 = ( (ri+0.5) / (R-ri+0.5) ) / ( (float(ni)-ri+0.5) / (N-float(ni)-R+ri+0.5) )
    factor2 = ( ((k1+1.0)*float(fi)) / (K+float(fi)) )
    factor3 = ( (k2+1.0)*float(qfi) ) / ( k2 + float(qfi) )
    return math.log(factor1) * factor2 * factor3

# C = collection size, D = number of words in document D, fqiD = frequency of query time i in D, cqi = frequency of word in collection
def QL_calc(fqiD, cqi, D):
    numerator = fqiD + mu * (cqi / abs(C))
    denominator = abs(D) + mu
    estimation = numerator/denominator
    return math.log(estimation)

def qfi_calc(term, qterms):
    count = 0
    for qterm in qterms:
        if qterm == term:
            count += 1
    return float(count)/float(len(qterms))
#print(qfi_calc("venice", ["venice", "venice", "on", "on", "the", "venice", "beach"]))


def rank(query):
    BM25_rankings = []
    QL_rankings = []
    BM25_pq = PriorityQueue()
    QL_pq = PriorityQueue()
    qterms = query.split(" ")
    for doc in range(1, getDocCount()+1):
        BM25_score = 0.0
        QL_score = 0.0
        K = K_calc(getDocLength(doc))
        for term in qterms:
            notFound = 0
            ni = float(getDocFreq(term))
            fi = float(getTermDocFreq(term, doc))
            if fi == 0.0:
                notFound += 1
                continue
            qfi = float(qfi_calc(term, qterms))
            cqi = float(getTermFreq(term))
            D = float(getDocLength(doc))
            BM25_termScore = BM25_calc(ni, fi, qfi, K)
            QL_termScore = QL_calc(fi, cqi, D)
            BM25_score += BM25_termScore
            QL_score += QL_termScore
        if notFound == len(qterms):
            continue
        if BM25_score != 0.0:
            BM25_pq.put((-BM25_score, doc))
            BM25_rankings.append((doc, BM25_score))
        if QL_score != 0.0:
            QL_pq.put((-QL_score, doc))
            QL_rankings.append((doc, QL_score))
    return BM25_pq, QL_pq
#rank("venice")
#print(BM25_rankings)  
#print(QL_rankings)
#while BM25_pq.empty() == False:
#    print(str(BM25_pq.get()))
#while QL_pq.empty() == False:
#    print(str(QL_pq.get()))

# start of queries
def Q1():
    return rank("the king queen royalty")
def Q2():
    return rank("servant guard soldier")
def Q3():
    return rank("hope dream sleep")
def Q4():
    return rank("ghost spirit")
def Q5():
    return rank("fool jester player")
def Q6():
    return rank("to be or not to be")
def runQueries():
    q1_BM25, q1_QL = Q1()
    q2_BM25, q2_QL = Q2()
    q3_BM25, q3_QL = Q3()
    q4_BM25, q4_QL = Q4()
    q5_BM25, q5_QL = Q5()
    q6_BM25, q6_QL = Q6()
    
    #opens and clears files)
    f_bm25 = open("bm25.trecrun", "w")
    f_bm25.truncate(0)
    f_bm25.close()
    f_ql = open("ql.trecrun", "w")
    f_ql.truncate(0)
    f_ql.close()
    
    writeRankings("Q1", q1_BM25, "bm25.trecrun", "BM25")
    writeRankings("Q2", q2_BM25, "bm25.trecrun", "BM25")
    writeRankings("Q3", q3_BM25, "bm25.trecrun", "BM25")
    writeRankings("Q4", q4_BM25, "bm25.trecrun", "BM25")
    writeRankings("Q5", q5_BM25, "bm25.trecrun", "BM25")
    writeRankings("Q6", q6_BM25, "bm25.trecrun", "BM25")
    
    writeRankings("Q1", q1_QL, "ql.trecrun", "QL")
    writeRankings("Q2", q2_QL, "ql.trecrun", "QL")
    writeRankings("Q3", q3_QL, "ql.trecrun", "QL")
    writeRankings("Q4", q4_QL, "ql.trecrun", "QL")
    writeRankings("Q5", q5_QL, "ql.trecrun", "QL")
    writeRankings("Q6", q6_QL, "ql.trecrun", "QL")
    
def writeRankings(topicNumber, pq, fileName, qtype):
    file = open(fileName, "a")
    rankPosition = 1
    while not pq.empty():
        score, doc = pq.get()
        line = (topicNumber + " skip " + str(getSceneId(doc)) + "\t" +  str(rankPosition) + " " + str(-score) + " " + "ldang-" + str(qtype) + "\n")
        file.write(line)
        rankPosition += 1

runQueries()

#test1, test2 = rank("venice")
#while not test1.empty():
#    print(test1.get())
#print(getPostings("soldier"))
#print(getDocLength(557))
#print(getTermDocFreq("soldier", 557))
#print(getPostings("venice"))
#print(getDocLength(3))
#print(getTermDocFreq("venice", 3))
#print(getPostings("hope"))
#print(getPostings("dream"))
#print(getPostings("sleep"))
"""
intersections = {}
hopePostings = getPostings("hope")
dreamPostings = getPostings("dream")
sleepPostings = getPostings("sleep")
for doc, positions in hopePostings:
    if doc not in intersections:
        intersections[doc] = 1
    else:
        intersections[doc] += 1
for doc, positions in dreamPostings:
    if doc not in intersections:
        intersections[doc] = 1
    else:
        intersections[doc] += 1
for doc, positions in sleepPostings:
    if doc not in intersections:
        intersections[doc] = 1
    else:
        intersections[doc] += 1
test_pq =  PriorityQueue()
for doc in intersections:
    test_pq.put((-intersections[doc], doc))
for i in range(100):
    val = test_pq.get()
    print(val)
    print(getSceneId(val[1]))
"""