from matplotlib import pyplot as plt
from librosa.display import waveshow
import matplotlib.image as mpimg

import librosa, streamlit as st
from config import VIS_PATH

def plot_wave(y, sr, filepath = VIS_PATH):
    fig, ax = plt.subplots()
    img = waveshow(y, sr=sr, x_axis='time', ax=ax)

    ax.set_facecolor("black")
    plt.axis("off")
    plt.savefig(filepath, bbox_inches="tight", facecolor="black")

    #return plt.gcf()

def displaySoundTrack(saved_song, filepath = VIS_PATH, frame_rate = None):
    y, sr = librosa.load(saved_song, sr = frame_rate)
    plot_wave(y, sr)

    im = mpimg.imread(filepath)
    col1, col2, col3 = st.columns([1,6,1])

    with col1:
        st.write("")

    with col2:
        st.image(im, width = 500, caption = "Your song made into a soundtrack")

    with col3:
        st.write("")