from tests.base import BaseTopazTest
from topaz.modules.ffi.buffer import W_BufferObject
from rpython.rtyper.lltypesystem.rffi import sizeof, LONG, ULONG

class TestBuffer(BaseTopazTest):

    sizes = {'char': 1,
                   'uchar': 1,
                   'short': 2,
                   'ushort': 2,
                   'int': 4,
                   'uint': 4,
                   'long': sizeof(LONG),
                   'ulong': sizeof(ULONG),
                   'long_long': 8,
                   'ulong_long': 8,
                   'float': 4,
                   'double': 8}

    def test_total(self, space):
        for key in TestBuffer.sizes:
            w_res = space.execute("""
            buffer = FFI::Buffer.new(:%s, 3)
            buffer.total
            """ % key)
            expected = TestBuffer.sizes[key]*3
            assert self.unwrap(space, w_res) == expected

    def test_instantiations(self, space):
        generic_init = "FFI::Buffer.%s(:int, 5)"
        total_should = TestBuffer.sizes['int']*5
        for init_method in ['new',
                            'new_inout',
                            'new_in',
                            'new_out',
                            'alloc_inout',
                            'alloc_in',
                            'alloc_out']:
            w_buffer = space.execute(generic_init % init_method)
            w_buffer_total = space.send(w_buffer, 'total')
            assert total_should == self.unwrap(space, w_buffer_total)

    def test_default_size_is_1(self, space):
        w_res = space.execute("FFI::Buffer.alloc_in(7).total")
        assert self.unwrap(space, w_res) == 7

    def test_puts_return_self(self, space):
        for put in ['put_char',
                    'put_uchar',
                    'put_ushort',
                    'put_uint',
                    'put_ulong_long']:
            w_array = space.execute("""
            buffer = FFI::Buffer.new(:char, 8)
            put_result = buffer.%s(0, 0)
            [buffer, put_result]
            """ % put)
            w_buffers = w_array.listview(space)
            assert w_buffers[0] is w_buffers[1]

    def test_put_and_get_char(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 3)
        buffer.put_char(0, -127)
        buffer.put_char(1, 0)
        buffer.put_char(2, 127)
        (0..2).map { |x| buffer.get_char(x) }
        """)
        res = [self.unwrap(space, w_x) for w_x in w_array.listview(space)]
        assert res == [-127, 0, 127]

    def test_put_and_get_uchar(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:uchar, 3)
        buffer.put_uchar(0, 255)
        buffer.put_uchar(1, 127)
        buffer.put_uchar(2, 0)
        (0..2).map { |x| buffer.get_uchar(x) }
        """)
        res = [self.unwrap(space, w_x) for w_x in w_array.listview(space)]
        assert res == [255, 127, 0]

    def test_put_and_get_short(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:short, 3)
        buffer.put_short(0, -(2**15 - 1))
        buffer.put_short(2, 2**15 - 1)
        buffer.put_short(4, 0)
        [0, 2, 4].map { |x| buffer.get_short(x) }
        """)
        res = [self.unwrap(space, w_x) for w_x in w_array.listview(space)]
        assert res == [-(2**15 - 1), 2**15 - 1, 0]

    def test_put_and_get_ushort(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:ushort, 3)
        buffer.put_ushort(0, 256**2 - 1)
        buffer.put_ushort(2, 256)
        buffer.put_ushort(4, 0)
        [0, 2, 4].map { |x| buffer.get_ushort(x) }
        """)
        res = [self.unwrap(space, w_x) for w_x in w_array.listview(space)]
        assert res == [256**2 - 1, 256, 0]

    def test_put_and_get_int(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:int, 3)
        buffer.put_int(0, -(2**31 - 1))
        buffer.put_int(4, 2**31 - 1)
        buffer.put_int(8, 0)
        [0, 4, 8].map { |x| buffer.get_int(x) }
        """)
        res = [self.unwrap(space, w_x) for w_x in w_array.listview(space)]
        assert res == [-(2**31 - 1), 2**31 - 1, 0]

    def test_put_and_get_uint(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:uint, 3)
        buffer.put_uint(0, 256**4 - 1)
        buffer.put_uint(4, 2222222222)
        buffer.put_uint(8, 0)
        [0, 4, 8].map { |x| buffer.get_uint(x) }
        """)
        res = [self.unwrap(space, w_x) for w_x in w_array.listview(space)]
        assert res == [256**4 - 1, 2222222222, 0]

    def test_put_and_get_ulong_long(self, space):
        maxi = 256**8 - 1
        w_array = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 12)
        (0..4).each { |x| buffer.put_ulong_long(x, %s) }
        (0..4).map { |x| buffer.get_ulong_long(x) }
        """  %  maxi)
        w_chars = w_array.listview(space)
        assert all([self.unwrap(space, w_res).tolong() == maxi
                    for w_res in w_chars])

    def test_put_returns_self(self, space):
        w_array = space.execute("""
        buffer = FFI::Buffer.new(:char, 1)
        put_result = buffer.put_bytes(0, 'a')
        [buffer, put_result]
        """)
        w_buffers = w_array.listview(space)
        assert w_buffers[0] is w_buffers[1]

    def test_put_and_get_bytes(self, space):
        for i in range(2):
            w_res = space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 11)
            buffer.put_bytes(in_i, 'Hi there!')
            buffer.get_bytes(in_i, 9)
            """.replace('in_i', str(i)))
            assert self.unwrap(space, w_res) == 'Hi there!'

    def test_put_bytes_index_and_length(self, space):
        w_res = space.execute("""
        buffer = FFI::Buffer.alloc_in(:char, 3)
        buffer.put_bytes(0, '0123456', 2, 3)
        buffer.get_bytes(0, 3)
        """)
        assert self.unwrap(space, w_res) == '234'

    def test_put_bytes_too_big_index_error(self, space):
        with self.raises(space, 'IndexError',
                         "Tried to start at index 3 of str 012"):
            space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 3)
            buffer.put_bytes(0, '012', 3)
            """)

    def test_put_bytes_negative_index_error(self, space):
        with self.raises(space, 'IndexError',
                         "Tried to start at index -1 of str 012"):
            space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 3)
            buffer.put_bytes(0, '012', -1)
            """)

    def test_put_bytes_length_error(self, space):
        with self.raises(space, 'IndexError',
                         "Tried to end at index 4 of str 0123"):
            space.execute("""
            buffer = FFI::Buffer.alloc_in(:char, 3)
            buffer.put_bytes(0, '0123', 1, 3)
            """)

    def test_write_bytes_is_put_bytes_with_offset_eq_0(self, space):
        w_res = space.execute("""
        buffer = FFI::Buffer.new(:char, 3)
        buffer.write_bytes('foo')
        buffer.get_bytes(0, 3)
        """)
        assert self.unwrap(space, w_res) == 'foo'
