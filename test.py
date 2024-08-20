import chromadb
client = chromadb.PersistentClient(path="./vectors")


collection = client.get_collection(name="test")

# get = client.get_collection(name="test")

# print(get)
# collection.add(
#     documents=[
#         "This is a document about pineapple",
#         "This is a document about oranges",
#         "this is a document about sex"
#     ],
#     ids=["id1", "id2", "id3"]
# )



results = collection.query(
    query_texts=["sex"], # Chroma will embed this for you
    n_results=1 # how many results to return
)
print(results)