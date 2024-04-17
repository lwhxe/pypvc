# pypvc
Most ridiculous lossless compression file format. Powered by Python.

The Python polynomial video codec (**PYPVC**) is created to compress video files into the smallest currently possible size in a realistic amount of time. Each channel, RGBa, is separated. And for that, each frame is separated. 
The pixels are sorted from left to right, row by row, then the RGBa values are checked and entered into each channel's list: r, g, b, a. A quadratic polynomial is then matched to each of the lists, each frame.
For an unused, 0, or NULL list entry, the entire list will be considered equal to NULL, and no coefficient will have to be assigned.
Multiprocessing is used to do each color simultaneously. (There are plans to check if using multithreading on the frames will make it go faster)
The alpha channel is currently not included.
This collected data is added to the .pypvc file. Audio is currently not accounted for. A media player is being developed.
