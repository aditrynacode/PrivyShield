import os
import pickle

MODEL_NAME = "distilbert-base-uncased"
DATA_DIR = "data"
OUTPUT_DIR = "models/ner_model"
ONNX_PATH = "models/ner_model.onnx"
MAX_LENGTH = 64
NUM_EPOCHS = 5
BATCH_SIZE = 16
LEARNING_RATE = 3e-5

def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)
 
def load_all_data():
    train_data = load_pickle(os.path.join(DATA_DIR, "train_data.pkl"))
    val_data = load_pickle(os.path.join(DATA_DIR, "val_data.pkl"))
    test_data = load_pickle(os.path.join(DATA_DIR, "test_data.pkl"))
    label_config = load_pickle(os.path.join(DATA_DIR, "label_config.pkl"))
    return train_data, val_data, test_data, label_config