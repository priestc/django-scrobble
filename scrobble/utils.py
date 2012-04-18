def chunks(data, chunksize=50):
    """
    Yield successive chunksize-sized chunks from data.
    """
    for i in xrange(0, len(data), chunksize):
        yield data[i:i+chunksize]