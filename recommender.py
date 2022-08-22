import pydub
from pydub import AudioSegment
from pydub.utils import mediainfo
import numpy as np
import math, itertools

from config import *

def db_to_float(db, using_amplitude=True):
    """
    Converts the input db to a float, which represents the equivalent
    ratio in power.
    """
    db = float(db)
    if using_amplitude:
        return 10 ** (db / 20)
    else:  # using power
        return 10 ** (db / 10)

class Recommender():
    def __init__(self, song):
        self.song = song
        self.faded = False
        self.count = 0
        self.bass_added = False
        self.recommendations = []

    def r_sample_rate(self):
        fr = self.song.frame_rate
        if fr < 30000:
            return f"Your song has a frame rate of {fr} Hz. You should definitely consider a higher frame rate. Head to the volume or speed up section. Apply a {44000/fr}"
        elif fr > 65000:
            return f"Your song has a frame rate of {fr} Hz. Your frame rate might be slightly too high. Feel free to adjust the speedup parameters by a factor of {44000/fr}"
        else: return f"Your song has a frame rate of {fr} Hz. You should be fine, change however you seem fit. "
        ## set_frame_rate()
        
    def cmpBS(self, bass_filename):
        clip = AudioSegment.from_wav(bass_filename)
        diff = self.song.frame_rate - clip.frame_rate 

        if diff > 10000:
            return f"There is a massive difference between your song's sample rate: {self.song.frame_rate} and your bass' sample rate {clip.frame_rate}. Please, adjust appropriately by setting a lower sample rate or applying gain to your bass track.  "

    def detect_silence(self, min_silence_len=1000, silence_thresh=-16, seek_step=1):
        """
        Returns a list of all silent sections [start, end] in milliseconds of audio_segment.
        Inverse of detect_nonsilent()
        audio_segment - the segment to find silence in
        min_silence_len - the minimum length for any silent section
        silence_thresh - the upper bound for how quiet is silent in dFBS
        seek_step - step size for interating over the segment in ms
        """
        seg_len = len(self.song)

        # you can't have a silent portion of a sound that is longer than the sound
        if seg_len < min_silence_len:
            return []

        # convert silence threshold to a float value (so we can compare it to rms)
        silence_thresh = db_to_float(silence_thresh) * self.song.max_possible_amplitude

        # find silence and add start and end indicies to the to_cut list
        silence_starts = []

        # check successive (1 sec by default) chunk of sound for silence
        # try a chunk at every "seek step" (or every chunk for a seek step == 1)
        last_slice_start = seg_len - min_silence_len
        slice_starts = range(0, last_slice_start + 1, seek_step)

        # guarantee last_slice_start is included in the range
        # to make sure the last portion of the audio is searched
        if last_slice_start % seek_step:
            slice_starts = itertools.chain(slice_starts, [last_slice_start])

        for i in slice_starts:
            audio_slice = self.song[i:i + min_silence_len]
            if audio_slice.rms <= silence_thresh:
                silence_starts.append(i)

        # short circuit when there is no silence
        if not silence_starts:
            return []

        # combine the silence we detected into ranges (start ms - end ms)
        silent_ranges = []

        prev_i = silence_starts.pop(0)
        current_range_start = prev_i

        for silence_start_i in silence_starts:
            continuous = (silence_start_i == prev_i + seek_step)

            # sometimes two small blips are enough for one particular slice to be
            # non-silent, despite the silence all running together. Just combine
            # the two overlapping silent ranges.
            silence_has_gap = silence_start_i > (prev_i + min_silence_len)

            if not continuous and silence_has_gap:
                silent_ranges.append([current_range_start,
                                    prev_i + min_silence_len])
                current_range_start = silence_start_i
            prev_i = silence_start_i

        silent_ranges.append([current_range_start,
                            prev_i + min_silence_len])

        ss = [ f"Silent range #{k}:    {silent_ranges[k][0]} - {silent_ranges[k][1]}" for k in range(len(silent_ranges)) ]
        return f"The Recommender has detect several silent areas. We encourage you to use the track cutter below to alternate these. {ss}"

    def to_fade(self):
        if not self.faded:
            return "We encourage you to use the fade in&out for all your songs. It creates a much smoother transtition. "
        
    def harmony(self):
        sound = np.asarray(self.song.get_array_of_samples(),dtype = np.int64)
        disruptions, score = 0, 1
        wheres = []
        for ind in range(len(sound)-1):
            if sound[ind+1] > sound[ind]:
                score += 1
                if score > 1 and sound[ind+1] < sound[ind]: 
                    disruptions += 1
                    wheres.append(ind)
            elif sound[ind+1] > sound[ind]:
                score += 1
                if score > 1 and sound[ind+1] > sound[ind]: 
                    disruptions += 1
                    wheres.append(ind)

        length = int(self.song.duration_seconds)
        if disruptions != 0:
            if length / disruptions > 4:
                ss = [f"\nFrom {k} to {k + float(length%disruptions)}" for k in wheres]
                return f"The Recommender found several harmonical disruptions we would like you to take a look at. {ss}"
        else: return "Your song has great harmony!"


    def assembleRecommendations(self):
        self.recommendations = [self.r_sample_rate(), self.to_fade(),  self.detect_silence(), self.harmony()]
        if self.bass_added: self.recommendations.append(self.cmpBS(bass_song))
    
    def getRecommendation(self):
        rec =  self.recommendations[self.count]
        d = self.count
        self.count = d + 1
        print(self.count)
        return rec

