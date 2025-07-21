import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

def load_dataset(path="Bess_data_final.csv"):
    return pd.read_csv(path)

def prepare_user_vector(df, basic_input, expert_input):
    user_input = {**basic_input, **expert_input}
    medians = {col: df[col].median() for col in df.columns if df[col].dtype in ['int64', 'float64']}

    cleaned_input = {}
    for k, v in user_input.items():
        if k in df.columns and k in medians:
            cleaned_input[k] = medians[k] if v == '' else float(v)

    valid_features = list(cleaned_input.keys())
    df_subset = df[valid_features].copy().astype(float)
    user_vector = np.array([cleaned_input[col] for col in df_subset.columns]).reshape(1, -1)

    scaler = MinMaxScaler()
    df_scaled = scaler.fit_transform(df_subset)
    user_df = pd.DataFrame(user_vector, columns=df_subset.columns)
    user_scaled = scaler.transform(user_df)

    # Define weights (increase weight for 'C-rate' and 'Capacity')
    weights = np.ones(df_scaled.shape[1])
    feature_names = df_subset.columns

    for i, feature in enumerate(feature_names):
        if feature.lower() in ['C-Rate', 'Capacity']:
            weights[i] = 10.0  # You can adjust this weight

    # Apply weights
    df_scaled_weighted = df_scaled * weights
    user_scaled_weighted = user_scaled * weights

    # Compute similarity
    similarities = cosine_similarity(user_scaled_weighted, df_scaled_weighted)[0]
    top_indices = np.argsort(similarities)[::-1][:10]
    top_recommendations = df.iloc[top_indices].copy()
    top_recommendations['similarity'] = similarities[top_indices]

    return top_recommendations, cleaned_input
