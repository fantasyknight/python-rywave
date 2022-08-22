import streamlit as st
import pandas as pd
import numpy as np, librosa
import librosa.display
import matplotlib.pyplot as plt

from pydub import AudioSegment
from visualizer import displaySoundTrack

from aibeats import DJ
from recommender import Recommender
from config import *
            


def app():
    st.title("AI BEATS\n\n\n")
    st.subheader("By Metawave\n")
    # st.markdown("""
    # <style>
    # body{
    #     font-family: "Bold Italic", italic, serif;
    # }
    # </style>
    # """,
    # unsafe_allow_html=True
    # )

    ## HANDLE VERIFICATION ## 
    username = st.text_input("Your Discord Username", value = '', key = "username")
    member_list = createMemberList()

    if username == '':
        st.write("Please enter your Discord username to gain access. ")
    elif not findUser(username, member_list):
        st.markdown("**I am sorry. The AIBeats App is exclusive to Metawave members. Try checking your Discord Username or contacting the Metawave Team accordingly.** ")

    else:
        st.markdown("**Yeaaah. You made it!** :smile: ")
        st.write("A very warm welcome to the AI Beats platform. The website is designed in a straightforward manner, and we'll try to escort you along the way. We encourage you to take a quick look around. Once, you upload your first piece of music, you should see the Functionality dropdown on your left. After that, it's game on. ")
        st.write("We hope this application helps you take a step forwards designing or even creating your own beats. May it prove to be as fun for you as it was for us to create it. ")
        st.write("Feel free to start by using one of your own tracks or head out to our [AI Sounds](https://soundcloud.com/user-554233840) for an inspiration. ")

        ## HANDLE TRACK UPLOADING ## 
        uploaded_track = st.file_uploader("Upload your own track", type = ['mp3', 'wav'])
        if uploaded_track is not None:
            bytes_data = uploaded_track.read()
            st.write(f"You have uploaded the following track {uploaded_track.name}")
            st.audio(bytes_data, format='audio/oog')

            with open(saved_song, 'wb') as f:
                f.write(bytes_data)

            song = AudioSegment.from_mp3(saved_song)
            if 'song' not in st.session_state:
                st.session_state['song'] = song

            track = song
            displaySoundTrack(saved_song, frame_rate = song.frame_rate)

            st.sidebar.title("Please, select the functionaltity you'd like to use. ")
            functionality = st.sidebar.selectbox('List', ["Nope, I'm good.", 'Fade In & Out', '8D', 'Bass Emphasized', 'VolumeUp', 'Apply Beat', 'Low Pass Filter', 'High Pass Filter', 'Stereo Gain','Cut', 'Add Noise'])
            
            ## INIT DJ and RECOMMENDER ##
            dj = DJ(song)
            recommender = Recommender(track)
            recommender.assembleRecommendations()

            ## HANDLE MODIFICATIONS ## 

            if functionality == "Nope, I'm good.":
                st.write("You are listening to the initial song without any modifications. Feel free to visit the dropdown on your left to play with the track. \n ")
            else: 
                st.markdown(f"<H2> {functionality} </H2>", unsafe_allow_html = True)
                track = dj.handleFunctionalities(functionality)
                dj.modifications_list.append(f"\n #{len(dj.modifications_list)}: {functionality} on {dj.interval[0]} : {dj.interval[1]} seconds")

           
            print(int(track.duration_seconds))
            ## BUTTONS ##
            downloadButton, playButton, initialButton = st.columns([1,1,1])
            infoButton, recButton, listButton = st.columns([1,1,1])

            with downloadButton:
                if st.button('DOWNLOAD'):
                    track.export(saved_song, format = "mp3")
                    st.write("Done. You should see the file in your bottom left corner. ")
            with playButton:
                if st.button('PLAY'):
                    byt = track.export()
                    #displaySoundTrack(saved_song,frame_rate = song.frame_rate)
                    st.audio(byt.read())
            with initialButton:
                if st.button('GET INITIAL TRACK'):
                    track = song
                    st.write("There you go, big fella. Gotcha. ")
            with infoButton:
                if st.button('BASIC INFO'):
                    data = getInfoOnTrack(track)
                    st.markdown(f"**Track information**: \n - Length: {data['Length']} seconds \n - Frame rate: {data['Frame_rate']} Hz \n - Channels: {data['Channels']}\n - Sample width: {data['Sample_Width']}\n - Bass Added: {dj.bass_added}")
            with recButton:
                if st.button('RECOMMEND'):
                    rec = recommender.getRecommendation()
                    st.markdown(f"**The AIBeats Recommender suggests the following:** \n - {rec}")
            with listButton:
                if st.button('SEE PAST LIST'):
                    ss = "**List of previously applied modifications:** \n"; 
                    for k in dj.modifications_list: ss += k
                    st.markdown(ss)
        
    st.write("\n\n\n")
    st.markdown('***Designed by the Metawave team.*** ')


                
        
if __name__ == '__main__':
    app()
