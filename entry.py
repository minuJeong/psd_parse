
import os
import struct


# DEBUG
def pick_psdfile():
    # Pick 1 psd file
    dirname = os.path.dirname(__file__).replace('\\', '/')
    target_file_path = None
    for filename in os.listdir():
        if not filename.endswith('.psd'):
            continue

        return f"{dirname}/{filename}"


class PSDParser(object):

    class _Version(object):
        """ 1 for psd files, 2 for psb files """

        is_psb = False

        def __init__(self, ispsb):
            assert ispsb == 1 or ispsb == 2
            self.is_psb = ispsb == 2

        def __repr__(self):
            return "PSB" if self.is_psb else "PSD"

    class _Depth(object):
        DEPTH_1 = 1
        DEPTH_8 = 8
        DEPTH_16 = 16
        DEPTH_32 = 32
        _valid_depths = [DEPTH_1, DEPTH_8, DEPTH_16, DEPTH_32]

        depth = None

        def __init__(self, key):
            assert key in self._valid_depths, f"Invalid color depth: {header_depth}"
            self.depth = key

        def __repr__(self):
            return f"{self.depth} bits"

    class _ColorMode(object):
        COLORMODE_BMP = 0
        COLORMODE_GRAY = 1
        COLORMODE_INDEXED = 2
        COLORMODE_RGB = 3
        COLORMODE_CMYK = 4
        COLORMODE_MULTICHANNEL = 7
        COLORMODE_DUOTONE = 8
        COLORMODE_LAB = 9
        _valid_colormodes = [COLORMODE_BMP, COLORMODE_GRAY, COLORMODE_INDEXED, COLORMODE_RGB,
                             COLORMODE_CMYK, COLORMODE_MULTICHANNEL, COLORMODE_DUOTONE, COLORMODE_LAB]

        _repr = {
            COLORMODE_BMP: "Bitmap",
            COLORMODE_GRAY: "Grayscale",
            COLORMODE_INDEXED: "Indexed Colors",
            COLORMODE_RGB: "RGB",
            COLORMODE_CMYK: "CMYK",
            COLORMODE_MULTICHANNEL: "Multi Channels",
            COLORMODE_DUOTONE: "Duotone",
            COLORMODE_LAB: "Lab Color"
        }

        mode = COLORMODE_RGB

        def __init__(self, key):
            assert key in self._valid_colormodes, f"Invalid color mode: {key}"
            self.mode = key

        def __repr__(self):
            if self.mode in self._repr:
                return self._repr[self.mode]

            return ""

    class _SIZE(object):
        width = None
        height = None

        def __init__(self, width, height, is_psb=False):
            maxsize = 300001 if is_psb else 30001
            assert height in range(1, maxsize) and \
                   width in range(1, maxsize), \
                   f"too big image for psb format: {height} : {width}"

            self.width = width
            self.height = height

        def __repr__(self):
            return f"({self.width}, {self.height})"

    class _PSD(object):
        version = None
        colordepth = None
        colormode = None
        size = None
        channelcount = 0

    @staticmethod
    def _read_header(result_file, bytes):
        if not result_file:
            return

        IDX_SIGNATURE = 4
        IDX_VERSION = 2
        IDX_RESERVED_ZEROS = 6
        IDX_CHANNEL_COUNT = 2
        IDX_IMG_HEIGHT = 4
        IDX_IMG_WIDTH = 4
        IDX_DEPTH = 2
        IDX_COLORMODE = 2

        cursor = 0
        def read_bytes(byte_count):
            nonlocal cursor
            data = bytes[cursor : cursor + byte_count]
            cursor = cursor + byte_count
            return [x for x in data]

        def join_bytes(bytes, convert_func=str):
            if convert_func:
                return "".join(map(lambda x: convert_func(x), bytes))

        # Read from bytes
        header_signature = str(join_bytes(read_bytes(IDX_SIGNATURE), chr))
        header_version = int(join_bytes(read_bytes(IDX_VERSION)))
        header_reserved_zero = str(join_bytes(read_bytes(IDX_RESERVED_ZEROS)))
        header_channelcount = int(join_bytes(read_bytes(IDX_CHANNEL_COUNT)))
        header_imgheight = int(join_bytes(read_bytes(IDX_IMG_HEIGHT)))
        header_imgwidth = int(join_bytes(read_bytes(IDX_IMG_WIDTH)))
        header_depth = int(join_bytes(read_bytes(IDX_DEPTH)))
        header_colormode = int(join_bytes(read_bytes(IDX_COLORMODE)))

        # Format validations
        assert header_signature == '8BPS', f"Wrong signature header: {header_signature}"
        assert header_version == 0 or int(header_version) == 1, f"Wrong version header: {header_version}"
        assert header_reserved_zero == '000000', f"Invalid reserved zeros: {header_reserved_zero}"
        assert header_channelcount in range(1, 57), f"Channel count out of bound: {header_channelcount}"

        # Assign parsed header information
        result_file.version = PSDParser._Version(header_version)
        result_file.colordepth = PSDParser._Depth(header_depth)
        result_file.colormode = PSDParser._ColorMode(header_colormode)
        result_file.size = PSDParser._SIZE(header_imgwidth, header_imgheight, header_version == 2)
        result_file.channelcount = header_channelcount

    @staticmethod
    def parse(filepath):
        result_file = PSDParser._PSD()
        with open(filepath, 'rb') as ff:
            PSDParser._read_header(result_file, ff.read(26))

        return result_file

print(PSDParser.parse(pick_psdfile()).__dict__)
