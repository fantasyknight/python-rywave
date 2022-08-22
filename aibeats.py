import pydub
from pydub import AudioSegment
import numpy as np
import math
import audioop
import streamlit as st

from pydub import AudioSegment
from pydub.generators import WhiteNoise

from config import *

### THE DJ CLASS HANDLES ALL THE SONG MODIFYING ### 
class DJ():
    def __init__(self, song):
        self.song = song
        self.interval = [0,0]
        self.partToWorkOn = song[self.interval[0]: self.interval[1]]
        self.modifiedPart = song
        self.faded = False
        self.bass_added = False

        self.modifications_list = []

    def songLength(self):
        return int(self.partToWorkOn.duration_seconds)

    def overlayPart(self):
        self.song[self.interval[0] : self.interval[1]] = self.modifiedPart
        return self.song

    def fade(self, in_duration = 0, out_duration = 0):
        return self.song.fade_in(in_duration*1000).fade_out(out_duration*1000)
    
    def bass_line_freq(self):
        sample_track = list(self.song)

        # c-value
        est_mean = np.mean(sample_track)

        # a-value
        est_std = 3 * np.std(sample_track) / (math.sqrt(2))

        bass_factor = int(round((est_std - est_mean) * 0.005))

        return bass_factor

    def make_chunks(self, chunk_length):
        number_of_chunks = math.ceil(len(self.song) / float(chunk_length))
        return [self.song[i * chunk_length:(i + 1) * chunk_length]
                for i in range(int(number_of_chunks))]

    def emphasise_bass(self, attentuate_db = ATTENUATE_DB, accentuate_db = ACCENTUATE_DB):
        
        filtered = self.low_pass_filter(self.bass_line_freq())
        self.modifiedPart = (self.partToWorkOn - attentuate_db).overlay(filtered + accentuate_db)
        return self.overlayPart()

    def volume_up(self, volume = 20):
        segment = self.partToWorkOn.apply_gain(volume)
        seg1, seg3 = self.song[:self.interval[0]], self.song[self.interval[1]:]

        return seg1.append(segment, crossfade = 0).append(seg3, crossfade = 0)

    def apply_bass(self, bass_filename, bass_volume = 10, position = 6000):
        self.bass_added = True
        clip = AudioSegment.from_mp3(bass_filename).apply_gain(bass_volume)
        return self.song.overlay(clip, position=position, times = 2)

    def low_pass_filter(self, cutoff):
        """
            cutoff - Frequency (in Hz) where higher frequency signal will begin to
                be reduced by 6dB per octave (doubling in frequency) above this point
        """
        RC = 1.0 / (cutoff * 2 * math.pi + 0.0001 )
        dt = 1.0 / FRAME_RATE

        alpha = dt / (RC + dt)
        
        original = self.partToWorkOn.get_array_of_samples()
        filteredArray = array.array(self.partToWorkOn.array_type, original)
        
        frame_count = int(self.partToWorkOn.frame_count())

        last_val = [0] * self.partToWorkOn.channels
        for i in range(self.partToWorkOn.channels):
            last_val[i] = filteredArray[i] = original[i]

        for i in range(1, frame_count):
            for j in range(self.partToWorkOn.channels):
                offset = (i * self.partToWorkOn.channels) + j
                last_val[j] = last_val[j] + (alpha * (original[offset] - last_val[j]))
                filteredArray[offset] = int(last_val[j])

        return self.partToWorkOn._spawn(data=filteredArray)

    def high_pass_filter(self, cutoff):
        """
            cutoff - Frequency (in Hz) where lower frequency signal will begin to
                be reduced by 6dB per octave (doubling in frequency) below this point
        """
        RC = 1.0 / (cutoff * 2 * math.pi +0.0001)
        dt = 1.0 / FRAME_RATE

        alpha = RC / (RC + dt)

        minval, maxval = get_min_max_value(self.partToWorkOn.sample_width * 8)
        
        original = self.partToWorkOn.get_array_of_samples()
        filteredArray = array.array(self.song.array_type, original)
        
        frame_count = int(self.partToWorkOn.frame_count())

        last_val = [0] * self.song.channels
        for i in range(self.song.channels):
            last_val[i] = filteredArray[i] = original[i]

        for i in range(1, frame_count):
            for j in range(self.song.channels):
                offset = (i * self.song.channels) + j
                offset_minus_1 = ((i-1) * self.song.channels) + j

                last_val[j] = alpha * (last_val[j] + original[offset] - original[offset_minus_1])
                filteredArray[offset] = int(min(max(last_val[j], minval), maxval))

        return self.partToWorkOn._spawn(data=filteredArray)

    def apply_gain_stereo(self, left_gain=0.0, right_gain=0.0):
        """
        left_gain - amount of gain to apply to the left channel (in dB)
        right_gain - amount of gain to apply to the right channel (in dB)
        
        note: mono audio segments will be converted to stereo
        """
        if self.song.channels == 1:
            left = right = self.partToWorkOn
        elif self.song.channels == 2:
            left, right = self.partToWorkOn.split_to_mono()
        
        l_mult_factor = db_to_float(left_gain)
        r_mult_factor = db_to_float(right_gain)
        
        left_data = audioop.mul(left._data, left.sample_width, l_mult_factor)
        left_data = audioop.tostereo(left_data, left.sample_width, 1, 0)
        
        right_data = audioop.mul(right._data, right.sample_width, r_mult_factor)
        right_data = audioop.tostereo(right_data, right.sample_width, 0, 1)
        
        output = audioop.add(left_data, right_data, self.song.sample_width)
        
        return self.partToWorkOn._spawn(data=output,
                    overrides={'channels': 2,
                            'frame_width': 2 * self.song.sample_width})

    def speedup(self, playback_speed=1.5, chunk_size=150, crossfade=25):
        atk = 1.0 / playback_speed

        if playback_speed < 2.0:
            # throwing out more than half the audio - keep 50ms chunks
            ms_to_remove_per_chunk = int(chunk_size * (1 - atk) / atk)
        else:
            # throwing out less than half the audio - throw out 50ms chunks
            ms_to_remove_per_chunk = int(chunk_size)
            chunk_size = int(atk * chunk_size / (1 - atk))

        # the crossfade cannot be longer than the amount of audio we're removing
        crossfade = min(crossfade, ms_to_remove_per_chunk - 1)

        chunks = self.make_chunks(chunk_size + ms_to_remove_per_chunk)
        if len(chunks) < 2:
            raise Exception("Could not speed up AudioSegment, it was too short {2:0.2f}s for the current settings:\n{0}ms chunks at {1:0.1f}x speedup".format(
                chunk_size, playback_speed, self.song.duration_seconds))

        ms_to_remove_per_chunk -= crossfade

        last_chunk = chunks[-1]
        chunks = [chunk[:-ms_to_remove_per_chunk] for chunk in chunks[:-1]]

        out = chunks[0]
        for chunk in chunks[1:]:
            out = out.append(chunk, crossfade=crossfade)

        out += last_chunk
        return out


    def cut_song(self, on_the_left_side, on_the_right_side):
        song = self.song[on_the_left_side:]
        song = self.song[:on_the_right_side]
        return self.song

    
    def addNoise(self):
        noise = WhiteNoise().to_audio_segment(duration=self.songLength)
        return self.partToWorkOn.overlay(noise)

    def transformto8D(self):
        adjust_jump, segment_length = 8, 200

        trap_song = self.song[0]
        pan_limit=[]
        limit_left  = -100

        for i in range(100):
            if int(limit_left) >= 100:
                break
            pan_limit.append(limit_left)
            limit_left+=adjust_jump

        pan_limit.append(100)

        for i in range(0,len(pan_limit)): pan_limit[i] = pan_limit[i] /100
        c=0
        flag = True

        for i in range(0,len(self.song)-segment_length, segment_length):

            peice = self.song[i:i+segment_length]

            if c==0 and not flag:
                flag =True
                c=c+2

            if c==len(pan_limit):
                c = c-2
                flag =False

            if flag:
                panned = peice.pan(pan_limit[c])
                c+=1

            else:
                panned = peice.pan(pan_limit[c])
                c-=1
            trap_song =trap_song+panned
            
        return trap_song
    
    def handleFunctionalities(self, functionality):
        if functionality == "Nope, I'm good.":
            st.write("You are listening to the initial song without any modifications. Feel free to visit the dropdown on your left to play with the track. ")
            return self.song
        else:
            st.write("Select the time interval upon which you want to apply the functionality. Play with the sliders above to choose different time interval. If left to default, the magic will be applied to the whole track, which is pretty cool as well if you ask me. ")

            self.interval[0] = int(st.text_input('Choose the first point of the time interval', 0))
            self.interval[1] = int(st.text_input('Choose the last point of the time interval',value = int(self.song.duration_seconds)))

            st.write(f"You have decided to apply {functionality} to your track. Play with the parameters to modify the song according to your wishes. ")
            if functionality == 'Low Pass Filter':
                cutoff = st.slider("Select the number of seconds of cutoff you'd like", 0, 50)
                return self.low_pass_filter(cutoff)

            elif functionality == 'High Pass Filter':
                cutoff = st.slider("Select the number of seconds of cutoff you'd like", 0, 50)
                return self.high_pass_filter(cutoff)

            elif functionality == 'Stereo Gain':
                left_gain = st.slider("Select the left gain stereo you'd like", 0, 200)
                right_gain = st.slider("Select the right gain stereo you'd like", 0, 200)
                return self.apply_gain_stereo(left_gain = left_gain, right_gain = right_gain)
            
            elif functionality == 'Bass Emphasized':
                attenuatedb = st.slider("Select attentuate db you'd like", 0, 100)
                accentuatedb = st.slider("Select accentuate db you'd like", 0, 100)
                return self.emphasise_bass(attentuate_db=attenuatedb, accentuate_db=accentuatedb)
            
            elif functionality == 'VolumeUp':
                volume = st.slider("Play with the volume mixer", -200, 200)
                return self.volume_up(volume)
            
            elif functionality == 'Add Noise':
                return self.addNoise()

            elif functionality == 'Bass':
                bass = st.file_uploader("Upload your own beat file to apply it", type = ['mp3', 'wav'])
                if bass is not None:
                    bytes_data = bass.read()
                    st.audio(bytes_data, format='audio/oog')

                    with open(bass_song, 'wb') as f:
                        f.write(bytes_data)

                    bass_volume = st.slider("Experiment with the Bass Volume", -100, 100)
                    return self.apply_bass(bass_song, bass_volume = bass_volume)

            elif functionality == 'Fade In & Out':
                fade_in = st.slider("Select the Fade In duration", 0.2, 10.0)
                fade_out = st.slider("Select the Fade Out duration", 0.2, 10.0)
                return self.fade(in_duration = int(float(fade_in)*1000), out_duration = int(float(fade_out)*1000))

            elif functionality == 'Cut':
                begin = st.slider("Select the beginning duration to cut", 0.0, 10.0)
                end = st.slider("Select the end duration to cut", 0.0, 10.0)
                return self.cut_song(begin, end)
            elif functionality == '8D':
                return self.transformto8D()