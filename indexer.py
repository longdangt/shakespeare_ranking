import json

inputFile = open("shakespeare-scenes.json")
fileData = json.load(inputFile)
dataset = fileData["corpus"]

"""
#dataset is lst of dicts with properties:
{
    playId,
    sceneId, 
    sceneNum,
    text
}
"""

# dict of term:posting[]
invertedIndex = {}
wordCount = 0
#create inverted index
for i in range(len(dataset)):
    docID = i+1
    docText = dataset[i]["text"].split(" ") # list of string vocab
    position = 1
    for j in range(len(docText)):
        term = docText[j]
        if len(term) >= 1:
            wordCount += 1
            if term in invertedIndex:
                postings = invertedIndex[term]
                docExists = False
                for k in range(len(postings)): 
                    if postings[k][0] == docID:
                        invertedIndex[term][k][1].append(position)
                        docExists = True
                if docExists == False:
                    invertedIndex[term].append((docID, [position]))
            else:
                invertedIndex[term] = [(docID, [position])]
            position += 1

#print(len(invertedIndex["fawn"]))

def return_docs_by_term(term):
    if term not in invertedIndex:
        return None
    docs = []
    for posting in invertedIndex[term]:
        docs.append(posting[0])
    return docs
#print(return_docs_by_term("where"))

def return_scenes_by_term(term):
    docs = return_docs_by_term(term)
    scenes = []
    for doc in docs:
        scenes.append(dataset[doc-1]["sceneId"])
    return scenes
#print(return_scenes_by_term("where"))
                            
def return_plays_by_term(term):
    scenes = return_scenes_by_term(term)
    plays = []
    for scene in scenes:
        play = scene.split(":")[0]
        if play not in plays:
            plays.append(play)
    return plays

def return_positions_by_term_and_doc(term, doc):
    if term not in invertedIndex:
        return None
    postings = invertedIndex[term]
    for posting in postings:
        if posting[0] == doc:
            return posting[1]
    return None

def return_scene_by_doc(doc):
    return dataset[doc-1]["sceneId"]

def return_play_by_doc(doc):
    return return_scene_by_doc(doc).split(":")[0]
#print(invertedIndex["where"])
#print(return_positions_by_doc("where", 1))
#print(return_plays_by_term("where"))
#print(invertedIndex["street"])
#print(return_scenes_by_term("denmark"))
#print(return_docs_by_term("street"))
#print(return_plays_by_term("street"))
#print(return_docs_by_term("yorick"))
print("Index Completed Running")

#writes invertedIndex to json file for later use
#https://stackabuse.com/reading-and-writing-json-to-a-file-in-python/
with open("invertedIndex.json", "w") as outputFile:
    json.dump(invertedIndex, outputFile)
