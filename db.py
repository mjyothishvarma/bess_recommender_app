from pymongo import MongoClient
import streamlit as st
def get_db():
    username = st.secrets['mongodb']['username']
    password = st.secrets["mongodb"]["password"]
    cluster = st.secrets["mongodb"]["cluster"]

    # uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
    client = MongoClient("mongodb://localhost:27017/")
    print("Atlas Connection successful")
    return client["bess_recommender"]["user_feedback"]

def save_feedback(cleaned_input, recommendations, user_feedback, user_name, user_email, global_comment):
    collection = get_db()
    document = {
        "name": user_name,
        "email": user_email,
        "user_input": cleaned_input,
        "recommendations": recommendations.to_dict(orient="records"),
        "feedback": user_feedback,
        "global_comment": global_comment
    }
    collection.insert_one(document)