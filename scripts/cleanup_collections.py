import chromadb

# def delete_code_collections(chroma_path="/mnt/f/projects/ai-recall-system/chroma_db"):
#     client = chromadb.PersistentClient(path=chroma_path)
    
#     # Print existing collections for reference
#     collections = client.list_collections()
#     print("🔎 Current collections in Chroma:")
#     for c in collections:
#         print(f" - {c}")

#     # The ones you want to remove
#     to_remove = {"project_codebase"}

#     # Try to delete them if they exist
#     for c in collections:
#         if c in to_remove:
#             try:
#                 client.delete_collection(c)
#                 print(f"✅ Deleted collection '{c}'")
#             except Exception as e:
#                 print(f"❌ Could not delete '{c}': {e}")

#     # Re-list collections after deletion
#     print("\n🔎 Collections after attempted deletion:")
#     collections_after = client.list_collections()
#     for c in collections_after:
#         print(f" - {c}")

# if __name__ == "__main__":
#     delete_code_collections()


def inspect_collections(chroma_path="/mnt/f/projects/ai-recall-system/chroma_db"):
    client = chromadb.PersistentClient(path=chroma_path)
    
    all_coll = client.list_collections()
    for coll_name in all_coll:
        coll = client.get_collection(coll_name)
        # Query some stats. If you just call coll.get() with no filter, you can see how many docs we have.
        data = coll.get()
        doc_count = len(data["documents"])
        print(f"Collection: {coll_name} => {doc_count} documents")

if __name__ == "__main__":
    inspect_collections()

