# Import dan Setup
import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import openai

# ----------------- Backend RAG & LLM -----------------

## Inisiasi Model Sentence Transformer
@st.cache_resource
def load_model():
    return SentenceTransformer('paraphrase-MiniLM-L6-v2')

model = load_model()

## FAISS & Cosine
def build_faiss_index_cosine(texts):
    # 1. Buat embedding
    embeddings = model.encode(texts, convert_to_numpy=True)

    # 2. Normalisasi agar inner product = cosine similarity
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings.astype('float32')  # FAISS hanya menerima float32

    # 3. Buat index FAISS dengan inner product
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    return index, embeddings

## Retrieval
def retrieve(query, index, df, top_k=None):
    return df  

## LLM - Generate Answer
def generate_answer(query, context, api_key):
    openai.api_key = api_key
    system_message = "Ensure your answer is relevant to the provided context."
    user_message = f"""
    Answer this question: {query}

    Based on the following information:
    {context}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0]['message']["content"].strip()

def transform_data(df, selected_columns):
    df["text"] = df[selected_columns].astype(str).agg(" | ".join, axis=1)
    return df   

# ----------------- UI -----------------

## Title Main Page
st.title("LLB: Building LLM Applications for Structured Data Insight")

## Sidebar
### Input Sidebar
st.sidebar.markdown(
    "<h2 style='text-align: center;'>Sidebar Menu</h2>",
    unsafe_allow_html=True
)

uploaded_file = st.sidebar.file_uploader("Upload File", type = 'csv')
input_api_key = st.sidebar.text_input("🕵🏻 Enter API Key", type = 'password')
button_api = st.sidebar.button('Activate API Key')

## Pengaturan Backend Sidebar
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

if input_api_key and button_api:
    st.session_state.api_key = input_api_key
    st.sidebar.success("API Key is Activated")

## Main Input
### Pengaturan Output File Setelah di Upload 
if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding='latin1')
    st.subheader("Choose Colomn")
    selected_columns = st.multiselect(
        "Choose Column that needs to be analyzed:",
        options = df.columns.to_list(),
        default = df.columns.to_list()
    )

    if not selected_columns:
        st.warning("⚠️ Choose at least 1 column.")
        st.stop()

    ### Tampilan Preview Kolom Yang Dipilih
    st.dataframe(df[selected_columns])

    ### Fungsi Menggabungkan Kolom
    # def transform_data(df, selected_columns):
    #     df["text"] = df[selected_columns].astype(str).agg(" | ".join, axis=1)
    #     return df   

    ### Input Pertanyaan Hanya Muncul Jika Kolom Telah Dipilih
    query = st.text_input("Enter your Question")
    run_query = st.button("Answer the Question")

    ### Menjalankan Semua Proses
    if run_query and st.session_state.api_key:
        try:
            df = transform_data(df, selected_columns)
            index, _ = build_faiss_index_cosine(df['text'].to_list())

            with st.spinner("Looking for Relevant Data"):
                results = retrieve(query, index, df)
                context = "\n".join(results["text"].to_list())

            with st.spinner("Providing Answer"):
                answer = generate_answer(query, context, st.session_state.api_key)

            st.subheader("💬 Answer:")
            st.success(answer)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    elif run_query and not st.session_state.api_key:
        st.warning("🔐 Please Activate API Key First.")
    else:
        st.warning("📂 Please Upload the CSV file first.")
