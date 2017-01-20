
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


    class _IMAGE_RESOURCE_BLOCK(object):

        uid = None
        name = None
        resource = None

        def __init__(self, uid, name, resource):
            self.uid = uid
            self.name = name
            self.resource = resource

        def __repr__(self):
            return f"UID: {self.uid}, NAME: {self.name}"


    class _PSD(object):

        # Header section
        version = None
        colordepth = None
        colormode = None
        size = None
        channelcount = 0

        # Image Resources section
        image_resource_blocks = []


    @staticmethod
    def _read_header(result_file, bytes):
        """basic information about psd file"""

        if not result_file:
            return

        # Const
        IDX_SIGNATURE = 4
        IDX_VERSION = 2
        IDX_RESERVED_ZEROS = 6
        IDX_CHANNEL_COUNT = 2
        IDX_IMG_HEIGHT = 4
        IDX_IMG_WIDTH = 4
        IDX_DEPTH = 2
        IDX_COLORMODE = 2

        # Util
        cursor = 0
        def read_bytes(byte_count, converter=str):
            nonlocal cursor
            data = bytes[cursor : cursor + byte_count]
            cursor = cursor + byte_count
            return ''.join(map(lambda x: converter(x), [x for x in data]))

        # Read
        header_signature = str(read_bytes(IDX_SIGNATURE, chr))
        header_version = int(read_bytes(IDX_VERSION))
        header_reserved_zero = str(read_bytes(IDX_RESERVED_ZEROS))
        header_channelcount = int(read_bytes(IDX_CHANNEL_COUNT))
        header_imgheight = int(read_bytes(IDX_IMG_HEIGHT))
        header_imgwidth = int(read_bytes(IDX_IMG_WIDTH))
        header_depth = int(read_bytes(IDX_DEPTH))
        header_colormode = int(read_bytes(IDX_COLORMODE))

        # Validation
        assert header_signature == '8BPS', f"Wrong signature header: {header_signature}"
        assert header_version == 0 or int(header_version) == 1, f"Wrong version header: {header_version}"
        assert header_reserved_zero == '000000', f"Invalid reserved zeros: {header_reserved_zero}"
        assert header_channelcount in range(1, 57), f"Channel count out of bound: {header_channelcount}"

        # Assign
        result_file.version = PSDParser._Version(header_version)
        result_file.colordepth = PSDParser._Depth(header_depth)
        result_file.colormode = PSDParser._ColorMode(header_colormode)
        result_file.size = PSDParser._SIZE(header_imgwidth, header_imgheight, header_version == 2)
        result_file.channelcount = header_channelcount

        return result_file


    @staticmethod
    def _read_colormode(result_file, bytes):
        """stores pallette for indexed color mode or
           in duotone mode, here's some undocumented specific data for duotone mode,
           according to adobe document, these data should just preserved as is."""

        if not result_file:
            return

        if not bytes:
            return

        raise Exception("[TODO] Indexed or Duotone mode is not supported!")


    @staticmethod
    def _read_imageresource(result_file, bytes):
        """stores non-pixel data, like pen-tool paths.
           after versions photoshop 5.0, stores thumbnail preview image here"""

        if not result_file:
            return

        # Const
        IDX_SIGNATURE = 4
        IDX_UID = 2
        IDX_RESOURCE_DATA_SIZE = 4

        # Util
        cursor = 0
        def read_bytes(byte_count, type_converter=lambda x: str(x), joiner = ''.join):
            nonlocal cursor
            data = bytes[cursor : cursor + byte_count]
            cursor = cursor + byte_count
            return joiner(list(map(type_converter, [x for x in data])))

        # Read
        signature = str(read_bytes(IDX_SIGNATURE, lambda x: chr(x)))
        uid = sum([int(ch) * pow(16, pos) for pos, ch in enumerate(read_bytes(IDX_UID)[::-1])])
        namechars = []

        name = read_bytes(2)
        while name != '00':
            namechars.append(name)
            name = read_bytes(2)
        img_res_block_name = ''.join(namechars)

        res_size = int(read_bytes(IDX_RESOURCE_DATA_SIZE))
        resources = read_bytes(res_size)

        # Validation
        assert signature == '8BIM', f"Invalid signature: {signature}"

        # Assign
        image_resource_block = PSDParser._IMAGE_RESOURCE_BLOCK(uid, name, resources)
        result_file.image_resource_blocks.append(image_resource_block)

        # TODO: PARSE_UID
        return result_file


    @staticmethod
    def parse(filepath):

        HEADER_BYTES = 26

        def _parse_int(bytes):
            return int.from_bytes(bytes, byteorder='big')

        result_file = PSDParser._PSD()
        with open(filepath, 'rb') as ff:
            PSDParser._read_header(result_file, ff.read(HEADER_BYTES))

            colormode_size = _parse_int(ff.read(4))
            if colormode_size:
                PSDParser._read_colormode(result_file, ff.read(colormode_size))

            imgres_size = _parse_int(ff.read(4))
            if imgres_size:
                PSDParser._read_imageresource(result_file, ff.read(imgres_size))

        return result_file

import json
parsed_psd = PSDParser.parse(pick_psdfile())
print(json.dumps(parsed_psd, indent=4, default=lambda o: o.__dict__, sort_keys=True))
