import array
from pydub import AudioSegment

INPUT_PATH = 'music/'
OUTPUT_PATH = 'nfts/'
LIST_PATH = 'list.txt'
JSON_PATH = 'metadata.json'
BASS_PATH = 'basses/'
VIS_PATH = "sound.png"
CLIP_LENGTH = 20
FADE_DURATION = 2
LOW_CUTOFF = 100
HIGH_CUTOFF = 200
VOLUME = 20
BASS_VOLUME = 10
ATTENUATE_DB = 0
ACCENTUATE_DB = 5
FRAME_RATE = 60

saved_song = 'song.mp3'
bass_song = 'bass.mp3'

# rarity je kater bass - beat ma neka pesem, to se skriva pod bass
features = ['Fade In & Out', 'Bass Emphasized', 'VolumeUp', 'Apply Beat', 'Low Pass Filter', 'High Pass Filter', 'Stereo Gain', '8D']


def song_length(filename):
    song = AudioSegment.from_mp3(filename)
    return int(song.duration_seconds)

def getInfoOnTrack(song):
    d = {}
    d["Length"] = int(song.duration_seconds)
    d['Frame_rate'] = song.frame_rate
    d['Channels'] = song.channels
    d['Sample_Width'] = song.sample_width

    return d

def createMemberList():
    with open(LIST_PATH, 'r') as f:
        return [line.split('\n')[0] for line in f.readlines()]

def findUser(username, list):
    for k in list:
        if k == username: return True
    return False

# dictf = {
#     "P1" : (lambda x: low_pass_filter()),
#     "P2" : (lambda x: high_pass_filter()),
#     "P3" : (lambda x: emphasise_bass()),
#     "P4" : (lambda x: volume_up()),
#     "P5" : (lambda x: apply_gain_stereo()),
#     "P6" : (lambda x: apply_basses()),
# }

items = ["P"+ str(k) for k in range(1, 7)]

def get_frame_width(bit_depth):
    return FRAME_WIDTHS[bit_depth]


def get_array_type(bit_depth, signed=True):
    t = ARRAY_TYPES[bit_depth]
    if not signed:
        t = t.upper()
    return t


def get_min_max_value(bit_depth):
    return ARRAY_RANGES[bit_depth]

FRAME_WIDTHS = {
    8: 1,
    16: 2,
    32: 4,
}

ARRAY_TYPES = {
    8: "b",
    16: "h",
    32: "i",
}
ARRAY_RANGES = {
    8: (-0x80, 0x7f),
    16: (-0x8000, 0x7fff),
    32: (-0x80000000, 0x7fffffff),
}

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
        