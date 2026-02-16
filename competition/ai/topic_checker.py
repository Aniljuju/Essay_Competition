from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_topic_score(topic, text):
    topic_vec = model.encode(topic, convert_to_tensor=True)
    essay_vec = model.encode(text, convert_to_tensor=True)

    return float(util.cos_sim(topic_vec, essay_vec))
