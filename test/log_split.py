
def splitMotionCorLog(outbuffer: list) -> dict:
    '''
    Takes the output from a motioncor2/motioncor3 run that uses the Serial flag and splits out the log
    outputs.
    '''
    log_split_buffer=[]
    outbuffers={}
    input_paths=[]
    header=[]
    footer=[]
    while outbuffer:
        line=outbuffer.pop(0)
        if line.startswith("added:"):
            input_paths.append(line.replace("added:", "").strip())
        if "Load Tiff movie:" in line:
            if not outbuffers and not header:
                header=log_split_buffer
            else:
                outbuffers[input_paths.pop(0)]=log_split_buffer
            log_split_buffer=[]
        if "Total time:" in line:
            outbuffers[input_paths.pop(0)]=log_split_buffer
            log_split_buffer=[]
            footer=log_split_buffer
        log_split_buffer.append(line)
    for k, v in outbuffers.items():
        outbuffers[k]=header+[""]+v+[""]+footer
    return outbuffers

def main():
    with open('./test_motioncorrection_utils/motioncor2_1.6.4_serial_log.txt', 'r') as f:
        outbuffer=f.readlines()

    outbuffer=[line.strip() for line in outbuffer]
    outbuffers=splitMotionCorLog(outbuffer)
    for k,v in outbuffers.items():
        print(k)
        print(v)

if __name__ == '__main__':
    main()